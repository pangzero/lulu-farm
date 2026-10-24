using UnityEngine;
using UnityEngine.EventSystems;

namespace LuluFarm
{
    public sealed class FarmTouchJoystick : MonoBehaviour, IPointerDownHandler, IDragHandler, IPointerUpHandler
    {
        public FarmInputRouter input;
        public RectTransform knob;
        public float radius = 65;
        int owner = int.MinValue;
        public void OnPointerDown(PointerEventData data)
        {
            if (owner != int.MinValue) return;
            owner = data.pointerId; OnDrag(data);
        }
        public void OnDrag(PointerEventData data)
        {
            if (owner != data.pointerId) return;
            Vector2 local;
            RectTransformUtility.ScreenPointToLocalPointInRectangle((RectTransform)transform, data.position, data.pressEventCamera, out local);
            Vector2 value = Vector2.ClampMagnitude(local / radius, 1);
            if (knob != null) knob.anchoredPosition = value * radius;
            if (input != null) input.TouchMove = value;
        }
        public void OnPointerUp(PointerEventData data) { if (owner == data.pointerId) ResetStick(); }
        void ResetStick() { owner = int.MinValue; if (input != null) input.TouchMove = Vector2.zero; if (knob != null) knob.anchoredPosition = Vector2.zero; }
        void OnDisable() { ResetStick(); }
        void OnApplicationFocus(bool focused) { if (!focused) ResetStick(); }
    }
}
