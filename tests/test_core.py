import base64
import unittest
import zlib

from backend.pob import BuildInputError, build_profile, decode_build
from backend.rules import classify, make_regex


XML = """<PathOfBuilding>
<Build targetVersion="3_0" level="100" className="Witch" ascendClassName="Occultist" mainSocketGroup="1">
  <PlayerStat stat="Life" value="1"/><PlayerStat stat="EnergyShield" value="10263"/>
  <PlayerStat stat="ChaosResist" value="-41"/><PlayerStat stat="ManaRegenRecovery" value="68.8"/>
  <PlayerStat stat="ManaPerSecondCost" value="193.68"/>
  <PlayerStat stat="EnergyShieldLeechGainRate" value="3029"/>
</Build>
<Skills activeSkillSet="1"><SkillSet id="1"><Skill enabled="true" mainActiveSkill="1">
  <Gem nameSpec="Winter Orb" enabled="true"/><Gem nameSpec="Frostbite" enabled="true"/>
  <Gem nameSpec="Discipline" enabled="true"/><Gem nameSpec="Animate Guardian" enabled="true"/>
</Skill></SkillSet></Skills>
<Items activeItemSet="1"><Item id="1">No reflection protection</Item>
<ItemSet id="1"><Slot name="Weapon 1" itemId="1"/></ItemSet></Items>
</PathOfBuilding>"""


def export_code(xml=XML):
    return base64.urlsafe_b64encode(zlib.compress(xml.encode())).decode().rstrip("=")


class BuildAnalysisTests(unittest.TestCase):
    def test_build_profile_and_map_decisions(self):
        profile = build_profile(decode_build(export_code()))
        self.assertEqual(profile["main_skill"], "Winter Orb")
        self.assertEqual(profile["energy_shield"], 10263)
        self.assertEqual(profile["chaos_resistance"], -41)
        mods = {mod["id"]: mod for mod in classify(profile)}
        self.assertEqual(mods["elemental_thorns"]["rating"], "review")
        self.assertEqual(mods["no_leech"]["rating"], "brick")
        self.assertEqual(mods["extra_chaos"]["rating"], "review")
        self.assertEqual(mods["physical_thorns"]["rating"], "free")
        self.assertEqual(mods["less_accuracy"]["rating"], "free")
        self.assertEqual(mods["hexproof"]["rating"], "free")

    def test_presets_and_override(self):
        mods = classify(build_profile(decode_build(export_code())))
        greedy = make_regex(mods, "greedy")
        balanced = make_regex(mods, "balanced")
        self.assertIn("cannot leech", greedy["query"])
        self.assertGreater(balanced["count"], greedy["count"])
        allowed = make_regex(mods, "greedy", {"no_leech": "allow"})
        self.assertNotIn("cannot leech", allowed["query"])
        self.assertTrue(balanced["within_limit"])

    def test_rejects_bad_input(self):
        with self.assertRaises(BuildInputError):
            decode_build("https://example.com/anything")
        with self.assertRaises(BuildInputError):
            decode_build(export_code("<not-a-build/>"))

    def test_cast_on_crit_build_blocks_reduced_cooldown(self):
        xml = """<PathOfBuilding>
        <Build className="Shadow" mainSocketGroup="1"/>
        <Skills activeSkillSet="1"><SkillSet id="1">
          <Skill mainActiveSkill="1"><Gem nameSpec="Cyclone" gemId="SkillGemCyclone"/>
            <Gem nameSpec="Cast On Critical Strike" gemId="SupportGemCastOnCrit"/>
            <Gem nameSpec="Forbidden Rite" gemId="SkillGemForbiddenRite"/></Skill>
        </SkillSet></Skills></PathOfBuilding>"""
        profile = build_profile(decode_build(export_code(xml)))
        self.assertTrue(profile["uses_cast_on_crit"])
        cooldown = next(mod for mod in classify(profile) if mod["id"] == "reduced_cooldown")
        self.assertEqual(cooldown["rating"], "brick")
        self.assertIn("Cast on Critical Strike", cooldown["reason"])

    def test_automated_mine_build_uses_damage_skill_and_blocks_cooldown(self):
        xml = """<PathOfBuilding>
        <Build className="Shadow" mainSocketGroup="1"/>
        <Skills activeSkillSet="1"><SkillSet id="1">
          <Skill mainActiveSkill="1"><Gem nameSpec="Empower" gemId="SupportGemAdditionalLevel"/>
            <Gem nameSpec="High-Impact Mine" gemId="SupportGemHighImpactMineSupport"/>
            <Gem nameSpec="Exsanguinate" gemId="SkillGemExsanguinate"/></Skill>
          <Skill><Gem nameSpec="Detonate Mines" gemId="SkillGemDetonateMines"/>
            <Gem nameSpec="Automation" gemId="SkillGemAutomation"/></Skill>
        </SkillSet></Skills></PathOfBuilding>"""
        profile = build_profile(decode_build(export_code(xml)))
        self.assertEqual(profile["main_skill"], "Exsanguinate")
        self.assertTrue(profile["uses_mines"])
        self.assertTrue(profile["automated_mine_detonation"])
        cooldown = next(mod for mod in classify(profile) if mod["id"] == "reduced_cooldown")
        self.assertEqual(cooldown["rating"], "brick")
        self.assertIn("manual detonation", cooldown["reason"])

    def test_high_block_gladiator_blocks_rust_affix(self):
        xml = """<PathOfBuilding><Build className="Duelist" ascendClassName="Gladiator" mainSocketGroup="1">
          <PlayerStat stat="EffectiveBlockChance" value="99.2"/>
          <PlayerStat stat="EffectiveSpellBlockChance" value="97.8048"/>
          <PlayerStat stat="Armour" value="36151"/>
          <PlayerStat stat="Evasion" value="0"/>
        </Build><Skills activeSkillSet="1"><SkillSet id="1"><Skill mainActiveSkill="1">
          <Gem nameSpec="Lacerate of Haemorrhage" gemId="Metadata/Items/Gems/SkillGemLacerate"/>
        </Skill></SkillSet></Skills></PathOfBuilding>"""
        profile = build_profile(decode_build(export_code(xml)))
        self.assertEqual(profile["attack_archetype"], "Bleed attack")
        self.assertEqual(profile["main_skill_kind"], "attack")
        self.assertIn("High block", profile["defence_archetypes"])
        self.assertIn("Armour", profile["defence_archetypes"])
        rust = next(mod for mod in classify(profile) if mod["id"] == "reduced_block_and_armour")
        self.assertEqual(rust["rating"], "brick")
        self.assertIn("99.2% effective attack block", rust["reason"])
        self.assertIn("30% less Armour", rust["reason"])
        self.assertIn("reduced chance to block", make_regex(classify(profile), "greedy")["query"])

    def test_block_affix_uses_defence_values_not_ascendancy(self):
        profile = build_profile(decode_build(export_code()))
        profile.update(effective_attack_block=25, effective_spell_block=0, armour=3000)
        rust = next(mod for mod in classify(profile) if mod["id"] == "reduced_block_and_armour")
        self.assertEqual(rust["rating"], "uncomfortable")
        profile.update(effective_attack_block=0, effective_spell_block=0, armour=25000)
        rust = next(mod for mod in classify(profile) if mod["id"] == "reduced_block_and_armour")
        self.assertEqual(rust["rating"], "dangerous")

    def test_mana_leech_is_central_when_cost_exceeds_regeneration(self):
        profile = build_profile(decode_build(export_code()))
        profile.pop("recovery_channels")
        profile.pop("saved_mana_cost_per_second")
        profile.update(life=4000, energy_shield=0, life_leech=300, life_regen=240,
                       energy_shield_leech=0, mana_cost_per_second=50, mana_regen=10,
                       mana_leech=60, mana_unreserved=70)
        from backend.build_signals import signal_by_id
        signals = signal_by_id(profile)
        self.assertEqual(signals["mana_leech"]["strength"], 3)
        self.assertEqual(signals["life_leech"]["strength"], 1)
        self.assertEqual({row["id"]: row for row in classify(profile)}["no_leech"]["rating"], "brick")
        profile["mana_leech"] = 0
        self.assertEqual({row["id"]: row for row in classify(profile)}["no_leech"]["rating"], "review")

    def test_stacked_evasion_and_suppression_counter(self):
        profile = build_profile(decode_build(export_code()))
        profile.update(evasion=24000, spell_suppression=100, armour=0,
                       effective_attack_block=0, effective_spell_block=0)
        rating = {row["id"]: row for row in classify(profile)}["reduced_suppression_and_evasion"]
        self.assertEqual(rating["rating"], "brick")
        self.assertIn("24,000 Evasion", rating["reason"])
        self.assertIn("100% effective spell suppression", rating["reason"])

    def test_wardloop_requires_multiple_independent_signals(self):
        xml = """<PathOfBuilding><Build mainSocketGroup="1"><PlayerStat stat="Ward" value="1300"/></Build>
        <Skills activeSkillSet="1"><SkillSet id="1"><Skill mainActiveSkill="1">
          <Gem nameSpec="Ice Spear" gemId="SkillGemIceSpear"/>
          <Gem nameSpec="Cast when Damage Taken" gemId="SupportGemCastWhenDamageTaken"/>
          <Gem nameSpec="Summon Skeletons" gemId="SkillGemSummonSkeletons"/>
        </Skill></SkillSet></Skills>
        <Items activeItemSet="1"><Item id="1">Heartbound Loop\nMoonstone Ring</Item>
        <ItemSet id="1"><Slot name="Ring 1" itemId="1"/></ItemSet></Items>
        </PathOfBuilding>"""
        profile = build_profile(decode_build(export_code(xml)))
        self.assertTrue(profile["wardloop_detected"])
        self.assertTrue(profile["has_minion_skills"])
        self.assertFalse(profile["minion_damage_primary"])
        self.assertEqual({row["id"]: row for row in classify(profile)}["reduced_cooldown"]["rating"], "brick")
        profile["wardloop_detected"] = False
        self.assertEqual({row["id"]: row for row in classify(profile)}["reduced_cooldown"]["rating"], "review")

    def test_primary_minions_distinct_from_utility(self):
        xml = """<PathOfBuilding><Build mainSocketGroup="1"/>
        <Skills activeSkillSet="1"><SkillSet id="1"><Skill mainActiveSkill="1">
        <Gem nameSpec="Summon Raging Spirit" gemId="SkillGemSummonRagingSpirit"/>
        </Skill></SkillSet></Skills></PathOfBuilding>"""
        profile = build_profile(decode_build(export_code(xml)))
        self.assertTrue(profile["minion_damage_primary"])
        self.assertEqual(next(row for row in profile["signals"] if row["id"] == "minions")["strength"], 3)

    def test_chaos_immunity_overrides_negative_resistance(self):
        xml = XML.replace('<PlayerStat stat="Life" value="1"/>',
                          '<PlayerStat stat="Life" value="1"/><PlayerStat stat="ChaosMaximumHitTaken" value="inf"/>')
        profile = build_profile(decode_build(export_code(xml)))
        self.assertTrue(profile["chaos_immune"])
        self.assertEqual({row["id"]: row for row in classify(profile)}["extra_chaos"]["rating"], "free")
        profile.update(life=4000, chaos_immune=False)
        self.assertEqual({row["id"]: row for row in classify(profile)}["extra_chaos"]["rating"], "brick")

    def test_no_regeneration_bricks_continuous_self_drain(self):
        xml = """<PathOfBuilding><Build mainSocketGroup="1">
          <PlayerStat stat="Life" value="10000"/>
          <PlayerStat stat="LifeRegenRecovery" value="2000"/>
          <PlayerStat stat="NetLifeRegen" value="600"/>
          <PlayerStat stat="TotalBuildDegen" value="1400"/>
        </Build><Skills activeSkillSet="1"><SkillSet id="1"><Skill mainActiveSkill="1">
          <Gem nameSpec="Righteous Fire" gemId="SkillGemRighteousFire"/>
        </Skill></SkillSet></Skills></PathOfBuilding>"""
        profile = build_profile(decode_build(export_code(xml)))
        signals = {row["id"]: row for row in profile["signals"]}
        self.assertEqual(signals["sustained_life_drain"]["strength"], 3)
        stasis = {row["id"]: row for row in classify(profile)}["no_regen"]
        self.assertEqual(stasis["rating"], "brick")
        self.assertIn("1400/s of saved ongoing Life loss", stasis["reason"])
        self.assertIn("cannot regen", make_regex(classify(profile), "greedy")["query"])

    def test_high_regeneration_without_self_drain_is_not_automatically_brick(self):
        profile = build_profile(decode_build(export_code()))
        profile.pop("recovery_channels")
        profile.update(life=10000, energy_shield=0, life_regen=2000,
                       life_net_regen=2000, energy_shield_regen=0, mana_regen=0)
        stasis = {row["id"]: row for row in classify(profile)}["no_regen"]
        self.assertEqual(stasis["rating"], "dangerous")

    def test_channelled_elemental_hits_can_trigger_thorns(self):
        xml = """<PathOfBuilding><Build mainSocketGroup="1">
          <PlayerStat stat="Life" value="1"/><PlayerStat stat="EnergyShield" value="14000"/>
          <PlayerStat stat="ColdResist" value="75"/><PlayerStat stat="FireResist" value="80"/>
          <PlayerStat stat="LightningResist" value="80"/><PlayerStat stat="EnergyShieldLeechGainRate" value="2400"/>
        </Build><Skills activeSkillSet="1"><SkillSet id="1"><Skill mainActiveSkill="1">
          <Gem nameSpec="Winter Orb" gemId="SkillGemWinterOrb"/>
          <Gem nameSpec="Focused Channelling" gemId="SupportGemFocusedChannelling"/>
        </Skill></SkillSet></Skills></PathOfBuilding>"""
        profile = build_profile(decode_build(export_code(xml)))
        self.assertTrue(profile["main_uses_channeling"])
        self.assertEqual(profile["main_hit_types"], ["elemental"])
        mods = {row["id"]: row for row in classify(profile)}
        self.assertEqual(mods["elemental_thorns"]["rating"], "dangerous")
        self.assertIn("Channelling does not prevent", mods["elemental_thorns"]["reason"])
        self.assertEqual(mods["physical_thorns"]["rating"], "free")

    def test_chaos_immunity_and_capped_chaos_resistance_are_free(self):
        profile = build_profile(decode_build(export_code()))
        profile.update(life=1, energy_shield=14000, chaos_immune=True, chaos_resistance=-60)
        self.assertEqual({row["id"]: row for row in classify(profile)}["extra_chaos"]["rating"], "free")
        profile.update(life=5000, energy_shield=0, chaos_immune=False, chaos_resistance=75)
        self.assertEqual({row["id"]: row for row in classify(profile)}["extra_chaos"]["rating"], "free")

    def test_armour_damage_scaling_is_evidence_for_rust(self):
        xml = """<PathOfBuilding><Build mainSocketGroup="1">
          <PlayerStat stat="Armour" value="1961521"/><PlayerStat stat="Life" value="1"/>
          <PlayerStat stat="EnergyShield" value="4282"/>
        </Build><Skills activeSkillSet="1"><SkillSet id="1"><Skill mainActiveSkill="1">
          <Gem nameSpec="Smite" gemId="SkillGemSmite"/>
        </Skill></SkillSet></Skills>
        <Items activeItemSet="1"><Item id="1">Replica Dreamfeather\n1% increased Attack Damage per 450 Armour</Item>
        <ItemSet id="1"><Slot name="Weapon 1" itemId="1"/></ItemSet></Items></PathOfBuilding>"""
        profile = build_profile(decode_build(export_code(xml)))
        self.assertTrue(profile["armour_scales_attack_damage"])
        self.assertEqual(profile["main_skill_kind"], "attack")
        mods = {row["id"]: row for row in classify(profile)}
        self.assertEqual(mods["reduced_block_and_armour"]["rating"], "brick")
        self.assertIn("Attack Damage per Armour", mods["reduced_block_and_armour"]["reason"])
        self.assertEqual(mods["physical_thorns"]["rating"], "free")

    def test_charge_theft_only_enters_safe_preset_for_stacked_generated_charges(self):
        profile = build_profile(decode_build(export_code()))
        profile.update(maximum_charges={"Power": 6, "Frenzy": 3, "Endurance": 3},
                       charge_generation={"Power": True, "Frenzy": False, "Endurance": False})
        mod = {row["id"]: row for row in classify(profile)}["charge_theft"]
        self.assertEqual(mod["rating"], "uncomfortable")
        self.assertIn("steal.*charges", make_regex(classify(profile), "safe")["query"])
        self.assertNotIn("steal.*charges", make_regex(classify(profile), "balanced")["query"])
        profile["charge_generation"]["Power"] = False
        self.assertEqual({row["id"]: row for row in classify(profile)}["charge_theft"]["rating"], "free")
        profile["configured_charges"] = {"Power": 6}
        self.assertEqual({row["id"]: row for row in classify(profile)}["charge_theft"]["rating"], "uncomfortable")

    def test_pathfinder_and_traitor_flask_charge_dependencies(self):
        xml = """<PathOfBuilding><Build mainSocketGroup="1" ascendClassName="Pathfinder"/>
        <Skills activeSkillSet="1"><SkillSet id="1"><Skill mainActiveSkill="1"><Gem nameSpec="Frenzy"/></Skill></SkillSet></Skills>
        <Tree activeSpec="1"><Spec nodes="51101,12345"/></Tree>
        <Items activeItemSet="1"><Item id="1">Granite Flask</Item><Item id="2">Quicksilver Flask</Item>
        <ItemSet id="1"><Slot name="Flask 1" itemId="1"/><Slot name="Flask 2" itemId="2"/></ItemSet></Items>
        </PathOfBuilding>"""
        profile = build_profile(decode_build(export_code(xml)))
        self.assertTrue(profile["nature_adrenaline"])
        self.assertEqual(profile["filled_flasks"], 2)
        self.assertEqual({row["id"]: row for row in classify(profile)}["reduced_flask_charges"]["rating"], "brick")
        profile.update(ascendancy="Raider", nature_adrenaline=False, flask_effect_investment=0)
        self.assertEqual({row["id"]: row for row in classify(profile)}["reduced_flask_charges"]["rating"], "free")
        profile.update(ascendancy="Pathfinder", flask_effect_investment=100)
        self.assertEqual({row["id"]: row for row in classify(profile)}["reduced_flask_charges"]["rating"], "brick")
        profile.update(traitor_likely=True, empty_flask_slots=3)
        self.assertEqual({row["id"]: row for row in classify(profile)}["reduced_flask_charges"]["rating"], "brick")

    def test_one_empty_flask_slot_and_balbala_is_brick(self):
        def build(with_fifth_flask=False):
            fifth_item = '<Item id="6">Life Flask</Item>' if with_fifth_flask else ''
            fifth_slot = '<Slot name="Flask 5" itemId="6"/>' if with_fifth_flask else ''
            xml = f'''<PathOfBuilding><Build ascendClassName="Raider" mainSocketGroup="1"/>
            <Skills activeSkillSet="1"><SkillSet id="1"><Skill mainActiveSkill="1"><Gem nameSpec="Frenzy"/></Skill></SkillSet></Skills>
            <Items activeItemSet="1"><Item id="1">Brutal Restraint\nDenoted service in the akhara of Balbala</Item>
            <Item id="2">Granite Flask</Item><Item id="3">Jade Flask</Item>
            <Item id="4">Ruby Flask</Item><Item id="5">Quicksilver Flask</Item>{fifth_item}
            <ItemSet id="1"><Slot name="Jewel 1" itemId="1"/>
            <Slot name="Flask 1" itemId="2"/><Slot name="Flask 2" itemId="3"/>
            <Slot name="Flask 3" itemId="4"/><Slot name="Flask 4" itemId="5"/>{fifth_slot}</ItemSet></Items>
            </PathOfBuilding>'''
            return build_profile(decode_build(export_code(xml)))

        one_empty = build()
        self.assertEqual(one_empty["empty_flask_slots"], 1)
        self.assertTrue(one_empty["traitor_likely"])
        traitor_mod = {row["id"]: row for row in classify(one_empty)}["reduced_flask_charges"]
        self.assertEqual(traitor_mod["rating"], "brick")
        self.assertIn("at least one empty flask slot", traitor_mod["reason"])
        full = build(with_fifth_flask=True)
        self.assertEqual(full["empty_flask_slots"], 0)
        self.assertFalse(full["traitor_likely"])
        self.assertEqual({row["id"]: row for row in classify(full)}["reduced_flask_charges"]["rating"], "free")

    def test_curse_crit_area_and_stun_require_build_evidence(self):
        profile = build_profile(decode_build(export_code()))
        profile.update(curse_dependent=False, crit_chance=49, crit_multiplier=400,
                       area_of_effect_increased=74, stun_dependent=False)
        ratings = {row["id"]: row["rating"] for row in classify(profile)}
        self.assertEqual(ratings["reduced_monster_curse_effect"], "free")
        self.assertEqual(ratings["monster_crit_reduction"], "uncomfortable")
        for key in ("less_player_aoe", "unstunnable_monsters"):
            self.assertEqual(ratings[key], "free")
        profile.update(curse_dependent=True, crit_chance=50, crit_multiplier=300,
                       area_of_effect_increased=75, stun_dependent=True)
        ratings = {row["id"]: row["rating"] for row in classify(profile)}
        self.assertEqual(ratings["reduced_monster_curse_effect"], "dangerous")
        self.assertEqual(ratings["monster_crit_reduction"], "uncomfortable")
        self.assertEqual(ratings["less_player_aoe"], "uncomfortable")
        self.assertEqual(ratings["unstunnable_monsters"], "brick")

    def test_anathema_impending_doom_and_boneshatter_are_detected(self):
        xml = """<PathOfBuilding><Build mainSocketGroup="1"><PlayerStat stat="CritChance" value="65"/>
        <PlayerStat stat="CritMultiplier" value="3.5"/><PlayerStat stat="AreaOfEffectIncrease" value="100"/>
        <PlayerStat stat="PowerChargesMax" value="6"/></Build>
        <Skills activeSkillSet="1"><SkillSet id="1"><Skill mainActiveSkill="1">
        <Gem nameSpec="Boneshatter"/><Gem nameSpec="Power Charge on Critical Strike"/>
        <Gem nameSpec="Impending Doom"/><Gem nameSpec="Frostbite"/></Skill></SkillSet></Skills>
        <Items activeItemSet="1"><Item id="1">Anathema</Item><ItemSet id="1"><Slot name="Ring 1" itemId="1"/></ItemSet></Items>
        </PathOfBuilding>"""
        profile = build_profile(decode_build(export_code(xml)))
        self.assertTrue(profile["stun_dependent"])
        self.assertFalse(profile["curse_dependent"])
        self.assertFalse(profile["core_hex_trigger"])
        self.assertEqual(profile["crit_multiplier"], 350)
        self.assertEqual(profile["area_of_effect_increased"], 100)
        self.assertTrue(profile["charge_generation"]["Power"])


if __name__ == "__main__":
    unittest.main()
