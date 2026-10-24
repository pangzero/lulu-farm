using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;

namespace LuluFarm
{
    public sealed class FarmRenderQualityR07:MonoBehaviour
    {
        public FarmRuntimeBootstrap runtime;public Volume globalVolume;
        VolumeProfile instance;Bloom bloom;string previous;
        void LateUpdate()
        {
            if(runtime==null||!runtime.Initialized||runtime.QualityLabel==previous)return;
            previous=runtime.QualityLabel;bool mobile=previous=="手机";
            if(instance==null&&globalVolume!=null){instance=globalVolume.profile;instance.TryGet(out bloom);}
            if(bloom!=null)bloom.active=!mobile;
            runtime.mainCamera.GetUniversalAdditionalCameraData().renderPostProcessing=true;
            runtime.mainCamera.allowHDR=!mobile;
            QualitySettings.shadowDistance=mobile?22:40;
        }
        void OnDestroy(){if(instance!=null)Destroy(instance);}
    }
}
