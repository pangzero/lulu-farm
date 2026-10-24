using System;
using System.IO;
using System.Linq;
using UnityEngine;

namespace LuluFarm.Editor
{
    // Independent test-route revision. Keeps existing geometry, controller and playback code intact.
    public static class FarmRouteClearanceR07
    {
        public static void Configure(FarmRuntimeBootstrap runtime)
        {
            Physics.SyncTransforms();
            var route = runtime.gameObject.AddComponent<FarmRoutePlayback>();
            route.runtime = runtime;
            route.waypoints = FarmRoutePlayback.OverviewR01Route(runtime.routeMarkers);
            var changed = route.waypoints.Where(p => p.name == "house-west-back" || p.name == "house-west-path").ToArray();
            if (changed.Length != 2) throw new InvalidOperationException("Expected the two inherited west-house intermediate points");
            foreach (var point in changed) point.position.x = -4.9f;
            var inheritedContact = Hits(runtime, new Vector3(-5.5f, .025f, 6.1f));
            var clear = Enumerable.Range(0, 31).SelectMany(i => Hits(runtime, new Vector3(-4.9f, .025f, 8.4f - i * .1f))).Distinct().ToArray();
            var record = new Record {
                utc = DateTime.UtcNow.ToString("o"),
                inheritedContact = inheritedContact,
                revisedSegmentContacts = clear,
                changed = changed,
                pointCount = route.waypoints.Length,
            };
            var folder = "Evidence/r07/" + FarmProjectBuilder.R07Task;
            Directory.CreateDirectory(folder);
            File.WriteAllText(folder + "/route-clearance-revision.json", JsonUtility.ToJson(record, true));
            if (clear.Length != 0) throw new InvalidOperationException("Revised diagnostic route still touches: " + string.Join(", ", clear));
        }
        static string[] Hits(FarmRuntimeBootstrap runtime, Vector3 root)
        {
            // Controller is height 1.14, radius .28; this static probe adds .02 horizontal clearance.
            // Only scenery bodies, ignoring the player's own controller, camera-only layer and triggers.
            return Physics.OverlapCapsule(root + Vector3.up * .31f, root + Vector3.up * .83f, .30f, ~(1 << 28), QueryTriggerInteraction.Ignore)
                .Where(c => !c.transform.IsChildOf(runtime.transform))
                .Select(c => PathOf(c.transform)).Distinct().ToArray();
        }
        static string PathOf(Transform t) => t.parent == null ? t.name : PathOf(t.parent) + "/" + t.name;
        [Serializable] sealed class Record {
            public string utc;
            public string purpose = "One observed loop stop at (-5.500028,.025,6.280326); inherited route tracks the north fence endpoint. Preserve collider and move only two intermediate route x coordinates -5.5 to -4.9. No teleport or gameplay change.";
            public string comparisonLimit = "D6 final route differs at two intermediate points from r06/D5/D2/D3/D4. Performance values are not a strictly identical-path A/B experiment.";
            public int pointCount;
            public string[] inheritedContact, revisedSegmentContacts;
            public FarmRouteWaypoint[] changed;
        }
    }
}
