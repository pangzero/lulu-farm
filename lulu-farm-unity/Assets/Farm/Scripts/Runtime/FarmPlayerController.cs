using UnityEngine;

namespace LuluFarm
{
    [DefaultExecutionOrder(-50)]
    [RequireComponent(typeof(CharacterController))]
    public sealed class FarmPlayerController : MonoBehaviour
    {
        public FarmInputRouter input;
        public FarmThirdPersonCamera cameraRig;
        public Transform visualRoot;
        public FarmAnimationBridge animationBridge;
        // Measured stride / cycle durations of the supplied height-1.2 Lulu locomotion derivative.
        public float walkSpeed = .5471864f;
        public float runSpeed = 1.2777705f;
        public float acceleration = 8f;
        public float turnRate = 540f;
        public float gravity = -18f;
        public Bounds worldBounds = new Bounds(Vector3.zero, new Vector3(60, 30, 50));
        public float rescueHeight = -8f;
        public Vector3 spawnPosition;
        public bool IsGrounded { get; private set; }
        public float ActualSpeed { get; private set; }
        public CollisionFlags LastCollision { get; private set; }
        public Vector3 Velocity { get; private set; }
        CharacterController capsule;
        Vector3 horizontalVelocity;
        float verticalVelocity;

        void Awake()
        {
            capsule = GetComponent<CharacterController>();
            spawnPosition = transform.position;
            if (visualRoot == null) visualRoot = transform;
        }

        void Update()
        {
            if (input == null || cameraRig == null) return;
            float frameDt = Time.deltaTime;
            if (frameDt <= 0f) return;
            Vector2 axes = input.Paused ? Vector2.zero : Vector2.ClampMagnitude(input.Move, 1f);
            Vector3 desired = Quaternion.Euler(0, cameraRig.Yaw, 0) * new Vector3(axes.x, 0, axes.y);
            float targetSpeed = input.Run ? runSpeed : walkSpeed;
            Vector3 beforeFrame = transform.position;
            LastCollision = CollisionFlags.None;
            // Preserve the entire game-time frame. Small collision steps must not discard locomotion
            // time while the animation graph advances by the full frame at low device frame rates.
            int substeps = Mathf.Max(1, Mathf.CeilToInt(frameDt / .05f));
            float dt = frameDt / substeps;
            for (int step = 0; step < substeps; step++)
            {
                horizontalVelocity = Vector3.MoveTowards(horizontalVelocity, desired * targetSpeed, acceleration * dt);
                if (horizontalVelocity.sqrMagnitude > .0025f)
                {
                    Quaternion facing = Quaternion.LookRotation(horizontalVelocity.normalized, Vector3.up);
                    visualRoot.rotation = Quaternion.RotateTowards(visualRoot.rotation, facing, turnRate * dt);
                }
                IsGrounded = capsule.isGrounded;
                if (IsGrounded && verticalVelocity < 0) verticalVelocity = -2f;
                verticalVelocity = Mathf.Max(-30f, verticalVelocity + gravity * dt);
                Vector3 beforeStep = transform.position;
                Vector3 motion = (horizontalVelocity + Vector3.up * verticalVelocity) * dt;
                Vector3 planned = beforeStep + motion;
                float margin = capsule.radius;
                motion.x = Mathf.Clamp(planned.x, worldBounds.min.x + margin, worldBounds.max.x - margin) - beforeStep.x;
                motion.z = Mathf.Clamp(planned.z, worldBounds.min.z + margin, worldBounds.max.z - margin) - beforeStep.z;
                CollisionFlags stepCollision = capsule.Move(motion);
                LastCollision |= stepCollision;
                if ((stepCollision & CollisionFlags.Above) != 0) verticalVelocity = Mathf.Min(verticalVelocity, 0f);
            }
            IsGrounded = capsule.isGrounded;
            Velocity = (transform.position - beforeFrame) / frameDt;
            ActualSpeed = new Vector2(Velocity.x, Velocity.z).magnitude;
            if (animationBridge != null) animationBridge.SetLocomotion(ActualSpeed, walkSpeed, runSpeed, IsGrounded);
            if (transform.position.y < rescueHeight) Teleport(spawnPosition);
        }

        public void Teleport(Vector3 position)
        {
            capsule = GetComponent<CharacterController>();
            capsule.enabled = false;
            transform.position = position;
            capsule.enabled = true;
            verticalVelocity = 0;
            horizontalVelocity = Vector3.zero;
            ActualSpeed = 0;
            if (cameraRig != null) cameraRig.SnapToTarget();
        }
    }
}
