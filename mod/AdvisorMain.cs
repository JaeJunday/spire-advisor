using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using System.Reflection;
using HarmonyLib;
using MegaCrit.Sts2.Core.Modding;
using MegaCrit.Sts2.Core.Nodes.Screens;
using MegaCrit.Sts2.Core.Nodes.Screens.CardSelection;
using MegaCrit.Sts2.Core.Nodes.Screens.Map;
using MegaCrit.Sts2.Core.Rewards;

namespace SpireAdvisor;

[ModInitializer(nameof(Initialize))]
public static class AdvisorMain
{
    public const string ModId = "SpireAdvisor";

    public static void Initialize()
    {
        try
        {
            var harmony = new Harmony(ModId);
            harmony.PatchAll(typeof(AdvisorMain).Assembly);
            StateWriter.Write(new Dictionary<string, object> { ["screen"] = "init", ["note"] = "SpireAdvisor loaded" });
        }
        catch (Exception ex)
        {
            try { File.AppendAllText(StateWriter.LogPath, "init failed: " + ex + "\n"); } catch { }
        }
    }

    static string IdOf(object idObj)
    {
        // ModelId{Category, Entry} -> "CARD.INFLAME" 형태. 세이브 파일과 같은 표기.
        try
        {
            var t = idObj.GetType();
            var cat = t.GetProperty("Category")?.GetValue(idObj)?.ToString();
            var entry = t.GetProperty("Entry")?.GetValue(idObj)?.ToString();
            if (!string.IsNullOrEmpty(entry))
                return string.IsNullOrEmpty(cat) ? entry : cat + "." + entry;
        }
        catch { }
        try { return idObj?.ToString() ?? ""; } catch { return ""; }
    }

    static string CardId(object card)
    {
        try
        {
            var id = card.GetType().GetProperty("Id")?.GetValue(card);
            if (id != null) return IdOf(id);
        }
        catch { }
        return "";
    }

    static object Field(object o, string name)
    {
        try { return o.GetType().GetField(name, BindingFlags.Instance | BindingFlags.NonPublic | BindingFlags.Public)?.GetValue(o); }
        catch { return null; }
    }

    [HarmonyPatch(typeof(NRewardsScreen), nameof(NRewardsScreen.Show))]
    internal static class RewardsPatch
    {
        public static void Postfix(NRewardsScreen __instance)
        {
            try
            {
                var cards = new List<string>();
                var relics = new List<string>();
                var potions = new List<string>();
                var set = Field(__instance, "_rewardsSet");
                var rewards = (set != null ? Field(set, "Rewards") : null) as IEnumerable;
                if (rewards == null)
                {
                    var prop = set?.GetType().GetProperty("Rewards");
                    rewards = prop?.GetValue(set) as IEnumerable;
                }
                foreach (var r in rewards ?? new List<object>())
                {
                    try
                    {
                        var tname = r.GetType().Name;
                        if (tname.Contains("Card"))
                        {
                            var list = Field(r, "_cards") as IEnumerable;
                            if (list == null)
                            {
                                var p = r.GetType().GetProperty("Cards");
                                list = p?.GetValue(r) as IEnumerable;
                            }
                            if (list != null) foreach (var c in list)
                                {
                                    var id = CardId(c);
                                    if (id != "") cards.Add(id);
                                }
                        }
                        else if (tname.Contains("Relic"))
                        {
                            var id = ReflectRewardId(r);
                            if (id != "") relics.Add(id);
                        }
                        else if (tname.Contains("Potion"))
                        {
                            var id = ReflectRewardId(r);
                            if (id != "") potions.Add(id);
                        }
                    }
                    catch { }
                }
                StateWriter.Write(new Dictionary<string, object>
                {
                    ["screen"] = "reward",
                    ["reward_options"] = cards,
                    ["relic_options"] = relics,
                    ["potion_options"] = potions,
                });
            }
            catch (Exception ex) { StateWriter.Trace("RewardsPatch: " + ex.Message); }
        }

        static string ReflectRewardId(object r)
        {
            var t = r.GetType();
            foreach (var fname in new[] { "_relic", "_potion", "_claimedRelic", "_claimedPotion", "Relic", "Potion" })
            {
                try
                {
                    var v = Field(r, fname);
                    if (v == null) v = t.GetProperty(fname)?.GetValue(r);
                    if (v == null) continue;
                    var id = v.GetType().GetProperty("Id")?.GetValue(v);
                    if (id != null) return IdOf(id);
                }
                catch { }
            }
            return "";
        }
    }

    [HarmonyPatch(typeof(NCardRewardSelectionScreen), nameof(NCardRewardSelectionScreen.AfterOverlayShown))]
    internal static class CardRewardShownPatch
    {
        public static void Postfix(NCardRewardSelectionScreen __instance)
        {
            try
            {
                var cards = new List<string>();
                foreach (var fname in new[] { "_options", "_extraOptions" })
                {
                    var list = Field(__instance, fname) as IEnumerable;
                    if (list != null) foreach (var c in list)
                        {
                            var id = CardId(c);
                            if (id != "") cards.Add(id);
                        }
                }
                if (cards.Count > 0)
                    StateWriter.Write(new Dictionary<string, object>
                    {
                        ["screen"] = "reward",
                        ["reward_options"] = cards,
                    });
                else
                    StateWriter.Touch("CardReward");
            }
            catch (Exception ex) { StateWriter.Trace("CardRewardShownPatch: " + ex.Message); }
        }
    }

    [HarmonyPatch(typeof(NMapScreen), nameof(NMapScreen.Open))]
    internal static class MapOpenPatch
    {
        public static void Postfix() { StateWriter.Touch("map"); }
    }
}
