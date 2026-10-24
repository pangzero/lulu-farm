using UnityEngine;

namespace LuluFarm
{
    public sealed class FarmCropStage : MonoBehaviour
    {
        public string assetId, species, seedlingSourceVersion, matureSourceVersion;
        public GameObject seedling;
        public GameObject mature;
        public bool IsMature { get; private set; } = true;
        public void SetMature(bool value)
        {
            IsMature = value;
            if (seedling != null) seedling.SetActive(!value);
            if (mature != null) mature.SetActive(value);
        }
    }
}
