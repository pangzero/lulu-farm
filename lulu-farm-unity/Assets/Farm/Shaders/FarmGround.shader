Shader "LuluFarm/FarmGround"
{
    Properties
    {
        _GrassBase("Reference grass base",Color)=(.48,.69,.20,1)
        _GrassLow("Soft cool grass patch",Color)=(.4272,.6486,.176,1)
        _GrassHigh("Soft warm grass patch",Color)=(.5136,.71415,.22,1)
        _RoadBase("Reference warm road",Color)=(.82,.62,.34,1)
        _RoadMode("Use road edge mask",Float)=0
        _RoadMask("Road union edge mask",2D)="white" {}
        _RoadMaskWorldRect("World XZ min and inverse extent",Vector)=(-18,-13,.0277778,.0384615)
        _FineGrain("Very subtle near-field grain",Range(0,.02))=.008
        _Smoothness("Matte surface",Range(0,1))=.12
        [HideInInspector] _BaseMap("Depth pass compatibility",2D)="white" {}
        [HideInInspector] _BaseColor("Depth pass compatibility",Color)=(1,1,1,1)
        [HideInInspector] _Cull("Cull",Float)=2
        [HideInInspector] _Cutoff("Cutoff",Float)=.5
        [HideInInspector] _Surface("Surface",Float)=0
    }
    SubShader
    {
        Tags { "RenderPipeline"="UniversalPipeline" "RenderType"="Opaque" "Queue"="Geometry" }
        Pass
        {
            Name "ForwardLit"
            Tags { "LightMode"="UniversalForward" }
            Cull Back ZWrite On
            HLSLPROGRAM
            #pragma target 3.0
            #pragma vertex vert
            #pragma fragment frag
            #pragma multi_compile_fog
            #pragma multi_compile _ _MAIN_LIGHT_SHADOWS _MAIN_LIGHT_SHADOWS_CASCADE _MAIN_LIGHT_SHADOWS_SCREEN
            #pragma multi_compile_fragment _ _SHADOWS_SOFT _SHADOWS_SOFT_LOW _SHADOWS_SOFT_MEDIUM _SHADOWS_SOFT_HIGH
            #pragma multi_compile_fragment _ _SCREEN_SPACE_OCCLUSION
            #pragma multi_compile _ _ADDITIONAL_LIGHTS_VERTEX _ADDITIONAL_LIGHTS
            #pragma multi_compile_fragment _ _ADDITIONAL_LIGHT_SHADOWS
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Lighting.hlsl"
            TEXTURE2D(_RoadMask); SAMPLER(sampler_RoadMask);
            CBUFFER_START(UnityPerMaterial)
            half4 _GrassBase, _GrassLow, _GrassHigh, _RoadBase;
            float4 _RoadMaskWorldRect;
            half _RoadMode, _FineGrain, _Smoothness;
            CBUFFER_END
            struct Attributes { float4 positionOS:POSITION; float3 normalOS:NORMAL; };
            struct Varyings { float4 positionCS:SV_POSITION; float3 positionWS:TEXCOORD0; half3 normalWS:TEXCOORD1; };
            Varyings vert(Attributes input)
            {
                Varyings output;
                output.positionWS=TransformObjectToWorld(input.positionOS.xyz);
                output.positionCS=TransformWorldToHClip(output.positionWS);
                output.normalWS=TransformObjectToWorldNormal(input.normalOS);
                return output;
            }
            float hash21(float2 p)
            {
                float3 q=frac(float3(p.x,p.y,p.x)*.1031);
                q+=dot(q,q.yzx+33.33);
                return frac((q.x+q.y)*q.z);
            }
            float pigment(float2 p)
            {
                float2 cell=floor(p), f=frac(p); f=f*f*(3-2*f);
                return lerp(lerp(hash21(cell),hash21(cell+float2(1,0)),f.x),
                    lerp(hash21(cell+float2(0,1)),hash21(cell+float2(1,1)),f.x),f.y);
            }
            half3 grassColor(float2 p, float fine)
            {
                // Broad 2–7 metre pigment groupings; no surface displacement or normal noise.
                float clouds=pigment(p*.22+float2(4.3,7.8))*.70+pigment(p*.43+float2(17.2,3.1))*.30;
                float mixValue=smoothstep(.23,.77,clouds);
                return lerp(_GrassLow.rgb,_GrassHigh.rgb,mixValue)*(1+fine);
            }
            half4 frag(Varyings input):SV_Target
            {
                // Compute fog per fragment: the large ground triangles can span
                // the linear fog clamp, so interpolated vertex fog creates bands.
                half fog=ComputeFogFactor(TransformWorldToHClip(input.positionWS).z);
                float2 p=input.positionWS.xz;
                float footprint=max(length(ddx(p)),length(ddy(p)));
                float fine=(pigment(p*14+float2(1.3,6.8))-.5)*_FineGrain*(1-smoothstep(.025,.08,footprint));
                half3 grass=grassColor(p,fine);
                half3 albedo=grass;
                if(_RoadMode>.5)
                {
                    float2 uv=(p-_RoadMaskWorldRect.xy)*_RoadMaskWorldRect.zw;
                    float roadWeight=SAMPLE_TEXTURE2D(_RoadMask,sampler_RoadMask,uv).r;
                    float tone=.965+.06*pigment(p*.44+float2(9.3,15.2));
                    half3 road=_RoadBase.rgb*(tone+fine*.35);
                    // Opaque mixing with identical world-sampled grass avoids transparency sorting.
                    albedo=lerp(grass,road,roadWeight);
                }
                InputData data=(InputData)0;
                data.positionWS=input.positionWS;
                data.normalWS=NormalizeNormalPerPixel(input.normalWS);
                data.viewDirectionWS=GetWorldSpaceNormalizeViewDir(input.positionWS);
                data.shadowCoord=TransformWorldToShadowCoord(input.positionWS);
                data.fogCoord=fog;
                data.bakedGI=SampleSH(data.normalWS);
                data.vertexLighting=VertexLighting(input.positionWS,data.normalWS);
                data.normalizedScreenSpaceUV=GetNormalizedScreenSpaceUV(input.positionCS);
                data.shadowMask=half4(1,1,1,1);
                SurfaceData surface=(SurfaceData)0;
                surface.albedo=albedo; surface.metallic=0; surface.specular=half3(.5,.5,.5);
                surface.smoothness=_Smoothness; surface.normalTS=half3(0,0,1);
                surface.occlusion=1; surface.alpha=1;
                half4 color=UniversalFragmentPBR(data,surface);
                color.rgb=MixFog(color.rgb,fog);
                return color;
            }
            ENDHLSL
        }
        UsePass "Universal Render Pipeline/Lit/ShadowCaster"
        UsePass "Universal Render Pipeline/Lit/DepthOnly"
        UsePass "Universal Render Pipeline/Lit/DepthNormals"
    }
}
