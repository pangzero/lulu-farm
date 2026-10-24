using System.Collections.Generic;
using UnityEngine;
using Unity.Cinemachine;

namespace LuluFarm
{
    [DefaultExecutionOrder(100)]
    public sealed class FarmThirdPersonCamera : MonoBehaviour
    {
        public Transform target;
        public Transform headingTarget;
        public FarmInputRouter input;
        public Camera outputCamera;
        public CinemachineBrain brain;
        public CinemachineCamera virtualCamera;
        public CinemachineThirdPersonFollow thirdPersonFollow;
        public Transform orbitTarget;
        public Vector3 targetOffset = new Vector3(0, .72f, 0);
        public float yaw = 0, pitch = 35, distance = 5.1f;
        public float minimumDistance = 2.5f, maximumDistance = 8.6f;
        public float minimumPitch = 15, maximumPitch = 55;
        public float followSmoothTime = .09f;
        public float collisionRadius = .2f;
        public float minimumCharacterDistance = 1.5f;
        public LayerMask obstructionLayers = ~0;
        public float Yaw => orbitTarget != null && initialized ? orbitTarget.eulerAngles.y : yaw;
        public float Pitch => orbitTarget != null && initialized ? orbitTarget.eulerAngles.x : pitch;
        public float RequestedDistance => distance;
        public float ActualDistance { get; private set; }
        public string ObstructionName { get; private set; } = "";
        public int CollisionBufferOverflows { get; private set; }
        public bool TargetVisible { get; private set; } = true;
        public bool SafetyFallbackBlocked { get; private set; }
        public bool UsingSafetyOrbit { get; private set; }
        public int ActiveFadeCount => activeOccluders.Count;
        public bool CinemachineIsLive => brain != null && virtualCamera != null && ReferenceEquals(brain.ActiveVirtualCamera, virtualCamera);
        Vector3 smoothedTarget, followVelocity;
        float actualDistanceVelocity;
        bool initialized;
        RaycastHit[] hits = new RaycastHit[64];
        Collider[] overlaps = new Collider[32];
        readonly HashSet<FarmCameraOccluder> activeOccluders = new HashSet<FarmCameraOccluder>();
        readonly HashSet<FarmCameraOccluder> neededOccluders = new HashSet<FarmCameraOccluder>();
        static readonly float[] SafetyYawOffsets = { 30, -30, 60, -60, 90, -90, 135, -135, 180 };
        Vector3 lastSafeCameraPosition;
        bool hasSafeCameraPosition;
        bool skipPreviousCorridor;

        void Awake()
        {
            if (outputCamera == null) outputCamera = GetComponent<Camera>();
            if (outputCamera != null) { outputCamera.orthographic = false; outputCamera.fieldOfView = 52; outputCamera.nearClipPlane = .08f; }
        }

        // Call during scene authoring as well as runtime setup, so the real Cinemachine rig is serialized.
        // MainCamera is written only by Brain. This component supplies its independent orbit target and safe distance.
        public void ConfigureCinemachine(Transform owner)
        {
            if (outputCamera == null) outputCamera = GetComponent<Camera>();
            if (outputCamera == null) return;
            outputCamera.orthographic = false;
            brain = outputCamera.GetComponent<CinemachineBrain>();
            if (brain == null) brain = outputCamera.gameObject.AddComponent<CinemachineBrain>();
            brain.UpdateMethod = CinemachineBrain.UpdateMethods.ManualUpdate;
            brain.BlendUpdateMethod = CinemachineBrain.BrainUpdateMethods.LateUpdate;
            brain.IgnoreTimeScale = true;
            brain.DefaultBlend = new CinemachineBlendDefinition(CinemachineBlendDefinition.Styles.Cut, 0);
            if (orbitTarget == null)
            {
                orbitTarget = new GameObject("LuluCameraOrbitTarget").transform;
                orbitTarget.SetParent(owner, false);
            }
            if (virtualCamera == null)
            {
                var rig = new GameObject("LuluCinemachineThirdPerson");
                rig.transform.SetParent(owner, false);
                virtualCamera = rig.AddComponent<CinemachineCamera>();
            }
            virtualCamera.Follow = orbitTarget;
            virtualCamera.LookAt = null;
            var lens = virtualCamera.Lens;
            lens.FieldOfView = 52;
            lens.NearClipPlane = .08f;
            lens.FarClipPlane = Mathf.Max(100, outputCamera.farClipPlane);
            virtualCamera.Lens = lens;
            thirdPersonFollow = virtualCamera.GetComponent<CinemachineThirdPersonFollow>();
            if (thirdPersonFollow == null) thirdPersonFollow = virtualCamera.gameObject.AddComponent<CinemachineThirdPersonFollow>();
            thirdPersonFollow.ShoulderOffset = Vector3.zero;
            thirdPersonFollow.VerticalArmLength = 0;
            thirdPersonFollow.CameraSide = .5f;
            thirdPersonFollow.Damping = Vector3.zero;
            thirdPersonFollow.CameraDistance = distance;
            // Our per-collider query handles selective fades; a second generic solver would collide with faded crowns again.
            var obstacles = thirdPersonFollow.AvoidObstacles;
            obstacles.Enabled = false;
            thirdPersonFollow.AvoidObstacles = obstacles;
            SnapToTarget();
        }

        public void SnapToTarget()
        {
            if (target == null) return;
            smoothedTarget = target.position + targetOffset;
            followVelocity = Vector3.zero;
            ActualDistance = distance;
            actualDistanceVelocity = 0;
            hasSafeCameraPosition = false;
            skipPreviousCorridor = true;
            if (orbitTarget != null) orbitTarget.SetPositionAndRotation(smoothedTarget, Quaternion.Euler(pitch, yaw, 0));
            if (virtualCamera != null) virtualCamera.PreviousStateIsValid = false;
            initialized = true;
        }

        public void Recenter()
        {
            yaw = headingTarget != null ? headingTarget.eulerAngles.y : target != null ? target.eulerAngles.y : 0;
            pitch = 35; distance = 5.1f;
        }

        static readonly int FadeFocusId = Shader.PropertyToID("_FarmFadeFocusWS");
        void LateUpdate()
        {
            if (target == null || outputCamera == null || brain == null || thirdPersonFollow == null || orbitTarget == null) return;
            if (!initialized) SnapToTarget();
            if (input != null && !input.Paused)
            {
                yaw = Mathf.Repeat(yaw + input.LookDegrees.x, 360);
                pitch = Mathf.Clamp(pitch - input.LookDegrees.y, minimumPitch, maximumPitch);
                distance = Mathf.Clamp(distance - input.ZoomSteps * .45f, minimumDistance, maximumDistance);
                if (input.ResetRequested) Recenter();
            }
            float dt = Mathf.Min(Time.unscaledDeltaTime, .05f);
            smoothedTarget = Vector3.SmoothDamp(smoothedTarget, target.position + targetOffset,
                ref followVelocity, followSmoothTime, Mathf.Infinity, dt);
            // OcclusionDither-r09 keeps a clear keyhole around this point; older fade shaders ignore it.
            Shader.SetGlobalVector(FadeFocusId, smoothedTarget);
            Quaternion orbit = Quaternion.Euler(pitch, yaw, 0);
            Vector3 backward = orbit * Vector3.back;
            float nearHalfHeight = outputCamera.nearClipPlane * Mathf.Tan(outputCamera.fieldOfView * Mathf.Deg2Rad * .5f);
            float radius = Mathf.Max(collisionRadius, nearHalfHeight * Mathf.Sqrt(1 + outputCamera.aspect * outputCamera.aspect));
            float framingDistance = Mathf.Min(distance, Mathf.Max(minimumCharacterDistance, radius * 3));
            neededOccluders.Clear();
            PrepareFades(smoothedTarget, backward, distance, radius, framingDistance);
            // Retain transparency while the actual camera is recovering/rotating out of a building.
            Vector3 oldOffset = outputCamera.transform.position - smoothedTarget;
            if (!skipPreviousCorridor && oldOffset.sqrMagnitude > .001f)
                PrepareFades(smoothedTarget, oldOffset.normalized, oldOffset.magnitude, radius, framingDistance);
            skipPreviousCorridor = false;

            ObstructionName = "";
            float clearDistance = ClearDistance(smoothedTarget, backward, distance, radius, out string obstruction);
            ObstructionName = obstruction;
            UsingSafetyOrbit = false;
            SafetyFallbackBlocked = false;
            if (clearDistance < framingDistance)
            {
                // Do not replace a real solid-wall distance with a minimum clamp: that would put
                // the camera through the wall. Seek a collision-free perspective orbit instead.
                UsingSafetyOrbit = true;
                bool found = false;
                for (int i = 0; i < SafetyYawOffsets.Length; i++)
                {
                    Quaternion candidateOrbit = Quaternion.Euler(pitch, yaw + SafetyYawOffsets[i], 0);
                    float candidate = ClearDistance(smoothedTarget, candidateOrbit * Vector3.back, distance, radius, out _);
                    if (candidate < framingDistance) continue;
                    orbit = candidateOrbit; backward = orbit * Vector3.back;
                    clearDistance = candidate; found = true; break;
                }
                if (!found)
                {
                    // A target trapped within a non-fading solid has no guaranteed visible orbit.
                    // Preserve a safe external camera point and expose the unresolved state rather
                    // than reporting a .3-unit close-up as success.
                    SafetyFallbackBlocked = true;
                    Vector3 safePoint = hasSafeCameraPosition ? lastSafeCameraPosition : outputCamera.transform.position;
                    Vector3 safeOffset = safePoint - smoothedTarget;
                    float safePitch = Mathf.Asin(safeOffset.normalized.y) * Mathf.Rad2Deg;
                    if (safeOffset.magnitude >= framingDistance && safeOffset.magnitude <= maximumDistance
                        && safePitch >= minimumPitch && safePitch <= maximumPitch && CameraPointClear(safePoint, radius))
                    {
                        backward = (safePoint - smoothedTarget).normalized;
                        orbit = Quaternion.LookRotation(-backward, Vector3.up);
                        clearDistance = (safePoint - smoothedTarget).magnitude;
                    }
                    else
                    {
                        // Keep the camera itself outside solids even if the target is trapped and
                        // no unobstructed line of sight exists. The diagnostic deliberately stays failed.
                        clearDistance = distance;
                        for (int i = -1; i < SafetyYawOffsets.Length; i++)
                        {
                            Quaternion candidateOrbit = Quaternion.Euler(pitch, yaw + (i < 0 ? 0 : SafetyYawOffsets[i]), 0);
                            Vector3 candidateDirection = candidateOrbit * Vector3.back;
                            if (!CameraPointClear(smoothedTarget + candidateDirection * distance, radius)) continue;
                            orbit = candidateOrbit; backward = candidateDirection; break;
                        }
                    }
                }
            }
            PrepareFades(smoothedTarget, backward, clearDistance, radius, framingDistance);
            foreach (var owner in activeOccluders)
                if (owner != null && !neededOccluders.Contains(owner)) owner.SetOccluded(false);
            activeOccluders.Clear();
            foreach (var owner in neededOccluders) activeOccluders.Add(owner);
            // Retraction is immediate; recovery is damped. A newly solved safety orbit must never
            // interpolate from the old, too-close distance through Lulu on its way to a safe point.
            if (clearDistance < ActualDistance || ActualDistance < framingDistance || UsingSafetyOrbit)
            { ActualDistance = clearDistance; actualDistanceVelocity = 0; }
            else ActualDistance = Mathf.SmoothDamp(ActualDistance, clearDistance, ref actualDistanceVelocity, .18f, Mathf.Infinity, dt);
            orbitTarget.SetPositionAndRotation(smoothedTarget, orbit);
            thirdPersonFollow.CameraDistance = ActualDistance;
            // Exactly once per rendered frame, after player movement and the independent orbit target update.
            brain.ManualUpdate();
            Vector3 viewport = outputCamera.WorldToViewportPoint(target.position + targetOffset);
            TargetVisible = !SafetyFallbackBlocked && viewport.z > outputCamera.nearClipPlane && viewport.x > 0 && viewport.x < 1 && viewport.y > 0 && viewport.y < 1;
            if (!SafetyFallbackBlocked && ActualDistance >= framingDistance && CameraPointClear(outputCamera.transform.position, radius))
            { lastSafeCameraPosition = outputCamera.transform.position; hasSafeCameraPosition = true; }
        }

        void PrepareFades(Vector3 origin, Vector3 direction, float length, float radius, float framingDistance)
        {
            foreach (var owner in FarmCameraOccluder.Active)
            {
                if (owner == null || !owner.HasSafeFadeMaterials || !owner.IntersectsViewCorridor(origin, direction, length, radius, out float entry)) continue;
                neededOccluders.Add(owner);
                owner.SetOccluded(true, entry - .08f < framingDistance);
            }
            // A conservative camera-only collider may extend beyond the renderer bounds.
            int count = Cast(origin, direction, length, radius);
            for (int i = 0; i < count; i++) PrepareColliderFade(hits[i].collider, hits[i].distance, framingDistance);
            int overlapCount = Overlap(origin, radius);
            for (int i = 0; i < overlapCount; i++) PrepareColliderFade(overlaps[i], 0, framingDistance);
        }

        void PrepareColliderFade(Collider collider, float entry, float framingDistance)
        {
            if (IsTarget(collider)) return;
            var owner = collider.GetComponentInParent<FarmCameraOccluder>();
            if (owner == null || !owner.isActiveAndEnabled || !owner.OwnsCollider(collider) || !owner.HasSafeFadeMaterials) return;
            neededOccluders.Add(owner);
            owner.SetOccluded(true, entry - .08f < framingDistance);
        }

        float ClearDistance(Vector3 origin, Vector3 direction, float length, float radius, out string obstacleName)
        {
            float result = length;
            obstacleName = "";
            foreach (var owner in FarmCameraOccluder.Active)
            {
                if (owner == null || !owner.HasSafeFadeMaterials || owner.AllowsCameraPassThrough || !owner.IntersectsViewCorridor(origin, direction, length, radius, out float entry)) continue;
                float limit = Mathf.Max(0, entry - .08f);
                if (limit < result) { result = limit; obstacleName = owner.name; }
            }
            int count = Cast(origin, direction, length, radius);
            for (int i = 0; i < count; i++)
            {
                if (CanIgnore(hits[i].collider)) continue;
                float limit = Mathf.Max(0, hits[i].distance - .08f);
                if (limit < result) { result = limit; obstacleName = hits[i].collider.name; }
            }
            int overlapCount = Overlap(origin, radius);
            for (int i = 0; i < overlapCount; i++)
                if (!CanIgnore(overlaps[i])) { result = 0; obstacleName = overlaps[i].name; break; }
            return result;
        }

        bool IsTarget(Collider collider) => collider == null || collider.transform == target || collider.transform.IsChildOf(target);
        bool CanIgnore(Collider collider)
        {
            if (IsTarget(collider)) return true;
            var owner = collider.GetComponentInParent<FarmCameraOccluder>();
            return owner != null && owner.isActiveAndEnabled && owner.HasSafeFadeMaterials && owner.OwnsCollider(collider) && owner.AllowsCameraPassThrough;
        }
        bool CameraPointClear(Vector3 point, float radius)
        {
            int count = Overlap(point, radius);
            for (int i = 0; i < count; i++) if (!CanIgnore(overlaps[i])) return false;
            return true;
        }
        int Cast(Vector3 origin, Vector3 direction, float length, float radius)
        {
            int count = Physics.SphereCastNonAlloc(origin, radius, direction, hits, length, obstructionLayers, QueryTriggerInteraction.Ignore);
            if (count == hits.Length)
            {
                CollisionBufferOverflows++;
                hits = Physics.SphereCastAll(origin, radius, direction, length, obstructionLayers, QueryTriggerInteraction.Ignore);
                count = hits.Length;
                // Reserve headroom so normal future queries stay allocation-free.
                System.Array.Resize(ref hits, Mathf.Max(64, count * 2));
            }
            return count;
        }
        int Overlap(Vector3 point, float radius)
        {
            int count = Physics.OverlapSphereNonAlloc(point, radius, overlaps, obstructionLayers, QueryTriggerInteraction.Ignore);
            if (count == overlaps.Length)
            {
                CollisionBufferOverflows++;
                overlaps = Physics.OverlapSphere(point, radius, obstructionLayers, QueryTriggerInteraction.Ignore);
                count = overlaps.Length;
                System.Array.Resize(ref overlaps, Mathf.Max(32, count * 2));
            }
            return count;
        }
        void OnDisable()
        {
            foreach (var owner in activeOccluders) if (owner != null) owner.SetOccluded(false);
            activeOccluders.Clear(); neededOccluders.Clear();
        }
    }

}
