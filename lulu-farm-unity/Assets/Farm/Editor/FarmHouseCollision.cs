using UnityEngine;

namespace LuluFarm.Editor
{
    public static partial class FarmProjectBuilder
    {
        static void HouseCollision(GameObject house)
        {
            if (house == null) return;
            // Measured against the selected S01 atlas-r01 at its 4.9-unit world height.
            // Coordinates belong to the unscaled prefab root, before the scene's yaw.
            // A whole-house shrunken AABB allowed the player to enter visible side/back walls.
            Box(house.transform, "HouseMainWall", new Vector3(-.34f, 1.6f, -.34f), new Vector3(2.92f, 3.2f, 2.92f));
            Box(house.transform, "HouseSideWing", new Vector3(1.75f, 1.12f, -.415f), new Vector3(1.30f, 2.24f, 2.77f));
            Box(house.transform, "HouseDoorPlatform", new Vector3(-.16f, .1875f, 1.37f), new Vector3(1.20f, .375f, .50f));
            Box(house.transform, "HouseSideStallCounter", new Vector3(-2.14f, .44f, -.39f), new Vector3(.70f, .88f, 1.78f));
            // Conservative two-tier roof envelope participates only in camera obstruction.
            // Layer 28 is excluded from player physics; the measured sloped roof remains unchanged.
            Box(house.transform, "HouseRoofCameraLower", new Vector3(.18f, 3.09f, -.34f), new Vector3(4.78f, 1.42f, 3.44f));
            Box(house.transform, "HouseRoofCameraUpper", new Vector3(-.56f, 4.35f, -.36f), new Vector3(3.26f, 1.14f, 3.16f));
            house.transform.Find("HouseRoofCameraLower").gameObject.layer = 28;
            house.transform.Find("HouseRoofCameraUpper").gameObject.layer = 28;
        }
    }
}
