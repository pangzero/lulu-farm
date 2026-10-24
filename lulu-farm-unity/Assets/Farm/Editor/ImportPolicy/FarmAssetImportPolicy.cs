using UnityEditor;
using UnityEngine;

namespace LuluFarm.Editor
{
    public sealed class FarmAssetImportPolicy : AssetPostprocessor
    {
        void OnPreprocessTexture()
        {
            if (!assetPath.StartsWith("Assets/Farm/Art/")) return;
            // Current user freezes Lulu model and its imported representation.
            if (assetPath.Contains("/Lulu/")) return;
            var importer = (TextureImporter)assetImporter;
            bool normal = assetPath.Contains("_normal");
            bool data = normal || assetPath.Contains("_mask") || assetPath.Contains("_occlusion");
            // glTFast 6.20 Normal.cginc reads raw texture RG (2*RG-1), not Unity's
            // DXT5nm/AG unpacking. NormalMap type swizzles channels and corrupts the
            // tangent-space direction. Keep glTF RGB encoding as linear data.
            importer.textureType = TextureImporterType.Default;
            importer.sRGBTexture = !data;
            importer.mipmapEnabled = true;
            importer.isReadable = false;
            importer.alphaSource = TextureImporterAlphaSource.FromInput;
            importer.wrapMode = TextureWrapMode.Repeat;
            importer.filterMode = FilterMode.Bilinear;
            importer.anisoLevel = 2;
            importer.textureCompression = TextureImporterCompression.CompressedHQ;
            // Desktop retains reviewed 2K atlases. Android's separate cap remains a device-test candidate.
            importer.maxTextureSize = assetPath.Contains("/Comparisons/") ? 4096 : 2048;
            var android = importer.GetPlatformTextureSettings("Android");
            android.name = "Android"; android.overridden = true;
            android.maxTextureSize = assetPath.Contains("/Lulu/") ? 2048 : 1024;
            android.format = normal ? TextureImporterFormat.ASTC_4x4 : TextureImporterFormat.ASTC_6x6;
            importer.SetPlatformTextureSettings(android);
        }
    }
}
