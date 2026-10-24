Shader "LuluFarm/FarmSky"
{
    Properties
    {
        _Horizon("Horizon", Color) = (0.62,0.80,0.85,1)
        _Zenith("Upper sky", Color) = (0.34,0.62,0.82,1)
        _Cloud("Soft cloud", Color) = (0.97,0.98,0.94,1)
        _CloudOpacity("Cloud opacity", Range(0,1)) = 0.74
    }
    SubShader
    {
        Tags { "Queue"="Background" "RenderType"="Background" "PreviewType"="Skybox" "RenderPipeline"="UniversalPipeline" }
        Cull Off ZWrite Off
        Pass
        {
            HLSLPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #pragma target 3.0
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
            CBUFFER_START(UnityPerMaterial)
            half4 _Horizon, _Zenith, _Cloud;
            half _CloudOpacity;
            CBUFFER_END
            struct Attributes { float4 positionOS : POSITION; };
            struct Varyings { float4 positionCS : SV_POSITION; float3 direction : TEXCOORD0; };
            Varyings vert(Attributes input)
            {
                Varyings output;
                output.positionCS = TransformObjectToHClip(input.positionOS.xyz);
                output.direction = input.positionOS.xyz;
                return output;
            }
            float ellipse(float2 p, float2 center, float2 radius)
            {
                return 1 - length((p - center) / radius);
            }
            float cloud(float angle, float elevation, float turn, float height, float scale)
            {
                float delta = angle - turn * 6.283185307;
                float2 p = float2(atan2(sin(delta), cos(delta)), elevation - height) / scale;
                float body = ellipse(p, float2(0,-.015), float2(.235,.055));
                body = max(body, ellipse(p,float2(-.115,.018),float2(.105,.070)));
                body = max(body, ellipse(p,float2(-.018,.065),float2(.102,.115)));
                body = max(body, ellipse(p,float2(.105,.035),float2(.090,.078)));
                return smoothstep(-.16,.16,body);
            }
            half4 frag(Varyings input) : SV_Target
            {
                float3 direction = normalize(input.direction);
                float height = saturate(direction.y);
                half3 color = lerp(_Horizon.rgb, _Zenith.rgb, pow(height,.62));
                float angle = atan2(direction.z,direction.x);
                float mask = cloud(angle,height,.02,.21,1.10);
                mask = max(mask,cloud(angle,height,.17,.31,.82));
                mask = max(mask,cloud(angle,height,.31,.16,.95));
                mask = max(mask,cloud(angle,height,.46,.29,1.14));
                mask = max(mask,cloud(angle,height,.62,.18,.78));
                mask = max(mask,cloud(angle,height,.76,.34,.96));
                mask = max(mask,cloud(angle,height,.91,.17,1.05));
                mask *= smoothstep(.025,.10,direction.y);
                half3 cloudColor = lerp(_Horizon.rgb, _Cloud.rgb, .82 + height * .18);
                return half4(lerp(color,cloudColor,mask * _CloudOpacity),1);
            }
            ENDHLSL
        }
    }
}
