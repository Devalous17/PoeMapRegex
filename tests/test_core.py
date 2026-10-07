import base64
import unittest
import zlib

from pob import BuildInputError, build_profile, decode_build
from rules import classify, make_regex


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
        self.assertEqual(mods["elemental_reflect"]["rating"], "brick")
        self.assertEqual(mods["no_leech"]["rating"], "brick")
        self.assertEqual(mods["extra_chaos"]["rating"], "dangerous")
        self.assertEqual(mods["physical_reflect"]["rating"], "review")
        self.assertEqual(mods["less_accuracy"]["rating"], "free")
        self.assertEqual(mods["hexproof"]["rating"], "dangerous")

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


if __name__ == "__main__":
    unittest.main()
