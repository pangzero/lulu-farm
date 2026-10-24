using System;
using System.IO;
using System.Linq;
using UnityEditor.SceneManagement;
using UnityEngine;
namespace LuluFarm.Editor
{
 public static class FarmCollisionDiagnostic
 {
  [Serializable] class Item { public string name;public int layer;public Vector3 center,size;public float distance; }
  [Serializable] class Report { public Vector3 origin; public Item[] overlaps,hits; }
  public static void Run()
  {
   EditorSceneManager.OpenScene("Assets/Farm/Scenes/FarmWorld.unity");Physics.SyncTransforms();
   var p=new Vector3(16.036049f,.025f,4.095405f);var bottom=p+Vector3.up*.28f;var top=p+Vector3.up*.86f;
   Func<Collider,Item> item=c=>new Item{name=c.transform.parent?.name+"/"+c.name,layer=c.gameObject.layer,center=c.bounds.center,size=c.bounds.size};
   var report=new Report{origin=p,overlaps=Physics.OverlapCapsule(bottom,top,.31f).Select(item).ToArray(),hits=Physics.CapsuleCastAll(bottom,top,.28f,Vector3.forward,4).Select(h=>{var i=item(h.collider);i.distance=h.distance;return i;}).ToArray()};
   File.WriteAllText("Evidence/east-bank-collision-diagnostic.json",JsonUtility.ToJson(report,true));
   var test=new GameObject("Temporary_capsule_diagnostic");var cc=FarmRuntimeBootstrap.EnsureCharacterCapsule(test);
   Physics.IgnoreLayerCollision(0,28,true);test.transform.position=p+Vector3.back;Physics.SyncTransforms();
   var positions=new System.Collections.Generic.List<string>();
   for(int i=0;i<180;i++){var flags=cc.Move(new Vector3(.001f,-.033f,.0213f));if(i%15==0)positions.Add(i+" "+test.transform.position.ToString("F5")+" "+flags);}
   File.WriteAllLines("Evidence/east-bank-capsule-move.txt",positions);UnityEngine.Object.DestroyImmediate(test);
  }
 }
}
