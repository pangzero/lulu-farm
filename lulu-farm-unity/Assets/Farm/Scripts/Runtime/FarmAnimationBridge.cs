using System;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Animations;
using UnityEngine.Playables;

namespace LuluFarm
{
    // Only explicit locomotion names are accepted. Diagnostic clips never become walking substitutes.
    public sealed class FarmAnimationBridge : MonoBehaviour
    {
        public Animator animator;
        public Animation legacyAnimation;
        public AnimationClip idleClip, walkClip, runClip;
        public float blendSeconds = .18f;
        public string Status { get; private set; } = "unbound";
        public string CurrentMotion { get; private set; } = "Idle";
        public bool HasLocomotion => idleClip != null && walkClip != null && runClip != null;
        PlayableGraph graph;
        AnimationMixerPlayable mixer;
        AnimationClipPlayable[] clips;
        readonly float[] weights = { 1, 0, 0 };
        readonly float[] wanted = { 1, 0, 0 };
        double gaitPhase, idleTime;
        float gaitFrequency;
        bool useLegacy;
        AnimationClip[] sourceClips;

        void Start() { Bind(); }
        public void Bind()
        {
            if (graph.IsValid()) graph.Destroy();
            if (animator == null) animator = GetComponentInChildren<Animator>(true);
            if (legacyAnimation == null) legacyAnimation = GetComponentInChildren<Animation>(true);
            var available = new List<AnimationClip>();
            if (animator != null && animator.runtimeAnimatorController != null)
                available.AddRange(animator.runtimeAnimatorController.animationClips);
            if (legacyAnimation != null)
                foreach (AnimationState state in legacyAnimation) available.Add(state.clip);
            foreach (AnimationClip clip in available)
            {
                string key = clip.name.ToLowerInvariant().Replace("_", "").Replace("-", "");
                if (key == "idle" || key == "luluidle") idleClip = idleClip != null ? idleClip : clip;
                if (key == "walk" || key == "luluwalk") walkClip = walkClip != null ? walkClip : clip;
                if (key == "run" || key == "lulurun") runClip = runClip != null ? runClip : clip;
            }
            if (!HasLocomotion)
            {
                Status = "missing_real_locomotion_clips";
                if (legacyAnimation != null) legacyAnimation.Stop();
                if (animator != null) animator.enabled = false;
                return;
            }
            useLegacy = idleClip.legacy && walkClip.legacy && runClip.legacy;
            sourceClips = new[] { idleClip, walkClip, runClip };
            if (useLegacy)
            {
                if (legacyAnimation == null && animator == null)
                { Status = "missing_imported_animation_binding_root"; useLegacy = false; return; }
                if (legacyAnimation == null) legacyAnimation = animator.gameObject.AddComponent<Animation>();
                if (animator != null) animator.enabled = false;
                legacyAnimation.enabled = true;
                legacyAnimation.playAutomatically = false;
                legacyAnimation.cullingType = AnimationCullingType.AlwaysAnimate;
                foreach (AnimationClip clip in sourceClips)
                {
                    legacyAnimation.AddClip(clip, clip.name);
                    legacyAnimation[clip.name].wrapMode = WrapMode.Loop;
                }
                legacyAnimation.Play(idleClip.name);
                Status = "legacy_real_clips_bound_visual_review_pending";
            }
            else if (!idleClip.legacy && !walkClip.legacy && !runClip.legacy)
            {
                if (animator == null && legacyAnimation == null)
                { Status = "missing_imported_animation_binding_root"; return; }
                if (animator == null) animator = legacyAnimation.gameObject.AddComponent<Animator>();
                animator.enabled = true;
                animator.applyRootMotion = false;
                animator.cullingMode = AnimatorCullingMode.AlwaysAnimate;
                if (legacyAnimation != null) legacyAnimation.enabled = false;
                graph = PlayableGraph.Create("LuluRealLocomotion");
                graph.SetTimeUpdateMode(DirectorUpdateMode.GameTime);
                mixer = AnimationMixerPlayable.Create(graph, 3);
                clips = new AnimationClipPlayable[3];
                for (int i = 0; i < 3; i++)
                {
                    clips[i] = AnimationClipPlayable.Create(graph, sourceClips[i]);
                    clips[i].SetApplyFootIK(false);
                    clips[i].SetSpeed(0);
                    graph.Connect(clips[i], 0, mixer, i);
                }
                AnimationPlayableOutput.Create(graph, "LuluMotion", animator).SetSourcePlayable(mixer);
                graph.Play();
                Status = "generic_real_clips_bound_visual_review_pending";
            }
            else Status = "mixed_legacy_and_generic_clips_rejected";
        }

        public void SetLocomotion(float speed, float walkSpeed, float runSpeed, bool grounded)
        {
            float moving = Mathf.Clamp01(speed / Mathf.Max(.2f, walkSpeed * .25f));
            float running = Mathf.InverseLerp(walkSpeed * 1.05f, runSpeed, speed);
            wanted[0] = 1 - moving;
            wanted[1] = moving * (1 - running);
            wanted[2] = moving * running;
            CurrentMotion = moving < .1f ? "Idle" : running > .5f ? "Run" : "Walk";
            float baseDuration = Mathf.Lerp(walkClip != null ? walkClip.length : 1f,
                runClip != null ? runClip.length : .65f, running);
            float pace = speed / Mathf.Max(.1f, Mathf.Lerp(walkSpeed, runSpeed, running));
            gaitFrequency = pace / Mathf.Max(.1f, baseDuration);
        }

        void Update()
        {
            if (!HasLocomotion) return;
            float dt = Time.deltaTime;
            float smoothing = 1 - Mathf.Exp(-dt / Mathf.Max(.01f, blendSeconds));
            for (int i = 0; i < 3; i++) weights[i] = Mathf.Lerp(weights[i], wanted[i], smoothing);
            gaitPhase = (gaitPhase + gaitFrequency * dt) % 1;
            idleTime = (idleTime + dt) % Math.Max(.01, idleClip.length);
            if (useLegacy && legacyAnimation != null)
            {
                for (int i = 0; i < 3; i++)
                {
                    var state = legacyAnimation[sourceClips[i].name];
                    state.enabled = true; state.speed = 0; state.weight = weights[i];
                    state.time = (float)(i == 0 ? idleTime : gaitPhase * sourceClips[i].length);
                }
            }
            else if (graph.IsValid())
            {
                for (int i = 0; i < 3; i++) mixer.SetInputWeight(i, weights[i]);
                clips[0].SetTime(idleTime);
                clips[1].SetTime(gaitPhase * walkClip.length);
                clips[2].SetTime(gaitPhase * runClip.length);
            }
        }

        void OnDestroy() { if (graph.IsValid()) graph.Destroy(); }
    }
}
