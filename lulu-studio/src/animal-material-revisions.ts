// Generated material manifest; cow head v4 overrides the visually insufficient v1 bake.
export const animalMaterialRevisions = [
  {
    "id": "cow",
    "name": "牛",
    "source": "public/models/animals/cow.glb",
    "source_sha256": "2291ffea3c1dc899352b1b7082ccc3e68c59fb5a65e988514092f53b056fbba6",
    "file": "public/models/animal-studies/cow-head-clean-v4.glb",
    "url": "/models/animal-studies/cow-head-clean-v4.glb",
    "bytes": 32330512,
    "version": "3a09e330",
    "sha256": "3a09e330319317f8a0856792530f63e06d83e7b357bc3ffb344e7c89eb800b0b",
    "roughness": 0.24,
    "normal_scale": 0.08,
    "specular": 0.2,
    "triangles": 163414,
    "eye_triangles": 2584,
    "eyes": [
      {
        "side": -1,
        "triangles": 1413,
        "depth": 0.014,
        "center": [
          -0.19125254452228546,
          0.33723074197769165,
          0.6587105393409729
        ],
        "min": [
          -0.24226801097393036,
          0.27296164631843567,
          0.6273309588432312
        ],
        "max": [
          -0.12588100135326385,
          0.4163059890270233,
          0.6881310343742371
        ]
      },
      {
        "side": 1,
        "triangles": 1171,
        "depth": 0.014,
        "center": [
          0.18213030695915222,
          0.3483654856681824,
          0.6604451537132263
        ],
        "min": [
          0.12346666306257248,
          0.27336767315864563,
          0.6253200173377991
        ],
        "max": [
          0.24236400425434113,
          0.4169343411922455,
          0.6884909272193909
        ]
      }
    ],
    "focus_box": [
      [
        -0.4770649001785529,
        1.3723111976097773,
        0.7801068150095033
      ],
      [
        0.47925601140899227,
        1.8529293728977108,
        1.1111840853529724
      ]
    ],
    "head_box": [
      [
        -0.7543837439224336,
        1.0218274983979114,
        0.48845826032965245
      ],
      [
        0.7565748551528729,
        2.2,
        1.3741732181608828
      ]
    ],
    "vertices_normals_uvs_unchanged": true,
    "texture_images_unchanged": false,
    "cow_head_bake": {
      "changed_pixels": 2876281,
      "fully_cleaned_pixels": 2529064,
      "cow_head_texture_baked": true
    },
    "source_verified": true,
    "visual_review": {
      "status": "checked-front-side-quarter",
      "final_user_acceptance": "pending",
      "supersedes_v1_head_cleanup_claim": true,
      "screenshots": "review/cow-head-cleanup-v2/v4-{view}.jpg",
      "remaining": "Major ear arc/scratches visibly reduced. Fine traces remain near horn/ear roots and temple. Body black patches are unchanged."
    },
    "head_material_revision": "v4",
    "previous_revision": {
      "file": "public/models/animals-refined/v1/cow.glb",
      "sha256": "98d461ac91bd54f60a2ceececb7f8d331aee9275da8fde0887171271338f8e77"
    },
    "cow_head_solid_material": {
      "method": "welded-vertex graph closing and conservative solid-black interior face assignment",
      "source": "v1 cow with original albedo median31 classification",
      "closeSteps": 7,
      "interiorBoundaryRings": 1,
      "weldedVertices": 81709,
      "solidTriangles": 24202,
      "texturedBodyTriangles": 136628,
      "repairedNodes": 59,
      "pinkProtectedNodes": 14490,
      "hornProtectedNodes": 8885,
      "creamProtectedNodes": 39517,
      "targetSRGB": 24,
      "targetLinear": 0.009134058702220787,
      "geometryPositionsNormalsUVsUnchanged": true,
      "visualAcceptance": "pending"
    }
  },
  {
    "id": "sheep",
    "name": "绵羊",
    "source": "public/models/animals/sheep.glb",
    "source_sha256": "c86582ba2bd9c1ac38f0587ea094fb9beef5d1c81af4e13cc977274afe352596",
    "file": "public/models/animals-refined/v1/sheep.glb",
    "url": "/models/animals-refined/v1/sheep.glb",
    "bytes": 22269736,
    "version": "708ed083",
    "sha256": "708ed083f02797e11f1a7b5b5d1219e3272389ddbbc23b2022e92bcb65dc6679",
    "roughness": 0.23,
    "normal_scale": 0.06,
    "specular": 0.18,
    "triangles": 328030,
    "eye_triangles": 2294,
    "eyes": [
      {
        "side": -1,
        "triangles": 1035,
        "depth": 0.011679046042263507,
        "center": [
          -0.23617321252822876,
          0.23820964992046356,
          0.746174693107605
        ],
        "min": [
          -0.2933403253555298,
          0.14674265682697296,
          0.705374002456665
        ],
        "max": [
          -0.1600780040025711,
          0.31283900141716003,
          0.7986676692962646
        ]
      },
      {
        "side": 1,
        "triangles": 1259,
        "depth": 0.014715871587395667,
        "center": [
          0.218045175075531,
          0.22353626787662506,
          0.7598769068717957
        ],
        "min": [
          0.15972299873828888,
          0.1474563330411911,
          0.7074577212333679
        ],
        "max": [
          0.2890640199184418,
          0.31378766894340515,
          0.800192654132843
        ]
      }
    ],
    "focus_box": [
      [
        -0.50012859952241,
        1.1760952675487621,
        0.8103032600641652
      ],
      [
        0.4925401751153964,
        1.6401291179899917,
        1.1510212533308972
      ]
    ],
    "head_box": [
      [
        -0.7891606076503819,
        0.8124342584047937,
        0.5040132499042002
      ],
      [
        0.7815721832433683,
        2.1797901271339604,
        1.2719530810023003
      ]
    ],
    "source_verified": true,
    "visual_review": {
      "status": "checked-front-side-quarter",
      "final_user_acceptance": "pending",
      "screenshots": "review/animal-materials-20261018/screenshots/sheep-{view}-{version}.jpg",
      "remaining": "Original eye-surface dents/creases and small soft reflections remain; geometry not edited."
    },
    "vertices_normals_uvs_unchanged": true,
    "texture_images_unchanged": true,
    "cow_head_bake": {}
  },
  {
    "id": "duck",
    "name": "小鸭",
    "source": "public/models/animals/duck.glb",
    "source_sha256": "284a05a7750c8ebfc0bee59baa4ae01dd60f89e2fc592d63ae412f8168599b3d",
    "file": "public/models/animals-refined/v1/duck.glb",
    "url": "/models/animals-refined/v1/duck.glb",
    "bytes": 15981164,
    "version": "4f7942c5",
    "sha256": "4f7942c5cdaa13584220eb5f100f345f2fef8ca9205dad4d92d57a44f07fdb44",
    "roughness": 0.22,
    "normal_scale": 0.06,
    "specular": 0.2,
    "triangles": 197276,
    "eye_triangles": 3449,
    "eyes": [
      {
        "side": -1,
        "triangles": 1555,
        "depth": 0.017838111147284508,
        "center": [
          -0.2768254280090332,
          0.4012118875980377,
          0.4856966435909271
        ],
        "min": [
          -0.34818601608276367,
          0.3177330195903778,
          0.4555153548717499
        ],
        "max": [
          -0.2008916586637497,
          0.5256286263465881,
          0.5183767080307007
        ]
      },
      {
        "side": 1,
        "triangles": 1894,
        "depth": 0.01720365434885025,
        "center": [
          0.27911806106567383,
          0.4303947389125824,
          0.4810766577720642
        ],
        "min": [
          0.19189132750034332,
          0.31795331835746765,
          0.4565410315990448
        ],
        "max": [
          0.34321269392967224,
          0.5251817107200623,
          0.5167067050933838
        ]
      }
    ],
    "focus_box": [
      [
        -0.49454969889764333,
        1.3640425891031307,
        0.41133067407510154
      ],
      [
        0.48979872119048173,
        1.8125098268136777,
        0.6689928226089074
      ]
    ],
    "head_box": [
      [
        -0.7720949852859975,
        0.9840964909543999,
        0.08694612057651173
      ],
      [
        0.7720949852859975,
        2.2000000689121766,
        0.9516235547080611
      ]
    ],
    "source_verified": true,
    "visual_review": {
      "status": "checked-front-side-quarter",
      "final_user_acceptance": "pending",
      "screenshots": "review/animal-materials-20261018/screenshots/duck-{view}-{version}.jpg",
      "remaining": "Original eye-surface dents/creases and small soft reflections remain; geometry not edited."
    },
    "vertices_normals_uvs_unchanged": true,
    "texture_images_unchanged": true,
    "cow_head_bake": {}
  },
  {
    "id": "chicken",
    "name": "鸡",
    "source": "public/models/animals/chicken.glb",
    "source_sha256": "99c9f1367a5a7973ddb5632fddff5b1c8ef19e332ecf21f9ee264fa852da6ddf",
    "file": "public/models/animals-refined/v1/chicken.glb",
    "url": "/models/animals-refined/v1/chicken.glb",
    "bytes": 18572464,
    "version": "b970b39e",
    "sha256": "b970b39e6f77b8350ab49bbc3a8ffb2d8c27fcc7e5f54076b94e63da3b878b16",
    "roughness": 0.24,
    "normal_scale": 0.06,
    "specular": 0.2,
    "triangles": 235116,
    "eye_triangles": 2257,
    "eyes": [
      {
        "side": -1,
        "triangles": 1121,
        "depth": 0.009802587144076823,
        "center": [
          -0.2168361246585846,
          0.3350062966346741,
          0.6217350363731384
        ],
        "min": [
          -0.28117334842681885,
          0.2508726716041565,
          0.5751410126686096
        ],
        "max": [
          -0.14259232580661774,
          0.4240333139896393,
          0.660426676273346
        ]
      },
      {
        "side": 1,
        "triangles": 1136,
        "depth": 0.010392914433032273,
        "center": [
          0.2165042757987976,
          0.3565598726272583,
          0.6137738823890686
        ],
        "min": [
          0.1425199955701828,
          0.2517150044441223,
          0.5717403292655945
        ],
        "max": [
          0.28019699454307556,
          0.4266183376312256,
          0.6557072997093201
        ]
      }
    ],
    "focus_box": [
      [
        -0.4169506093249556,
        1.286502319207933,
        0.5479323670692583
      ],
      [
        0.4170311299391036,
        1.6977825890169844,
        0.8354405440132688
      ]
    ],
    "head_box": [
      [
        -0.7204620009543324,
        0.9065520036248842,
        0.2235431275325373
      ],
      [
        0.7205425215684804,
        2.2,
        1.0483751574657711
      ]
    ],
    "source_verified": true,
    "visual_review": {
      "status": "checked-front-side-quarter",
      "final_user_acceptance": "pending",
      "screenshots": "review/animal-materials-20261018/screenshots/chicken-{view}-{version}.jpg",
      "remaining": "Original eye-surface dents/creases and small soft reflections remain; geometry not edited."
    },
    "vertices_normals_uvs_unchanged": true,
    "texture_images_unchanged": true,
    "cow_head_bake": {}
  },
  {
    "id": "pig",
    "name": "粉猪",
    "source": "public/models/animals/pig.glb",
    "source_sha256": "86c54dca52e767bab127a661985d30ca5ff38a9f60cdc5943f80de1637dac2f3",
    "file": "public/models/animals-refined/v1/pig.glb",
    "url": "/models/animals-refined/v1/pig.glb",
    "bytes": 14795612,
    "version": "c85bf23b",
    "sha256": "c85bf23b3df0450e5df72f9feee9df09dc6993e63e9c42773bf5b95666ea3bb4",
    "roughness": 0.24,
    "normal_scale": 0.08,
    "specular": 0.18,
    "triangles": 178694,
    "eye_triangles": 2842,
    "eyes": [
      {
        "side": -1,
        "triangles": 1080,
        "depth": 0.008,
        "center": [
          -0.2692559063434601,
          0.20364421606063843,
          0.6707412600517273
        ],
        "min": [
          -0.3288939893245697,
          0.14540965855121613,
          0.6248000264167786
        ],
        "max": [
          -0.19854168593883514,
          0.30723264813423157,
          0.7018319964408875
        ]
      },
      {
        "side": 1,
        "triangles": 1762,
        "depth": 0.009429544769227504,
        "center": [
          0.22749997675418854,
          0.23923173546791077,
          0.6775484681129456
        ],
        "min": [
          0.1931636780500412,
          0.14453667402267456,
          0.6235139966011047
        ],
        "max": [
          0.3279479742050171,
          0.3051076829433441,
          0.7064070701599121
        ]
      }
    ],
    "focus_box": [
      [
        -0.7253439233147772,
        1.198284195472937,
        0.9308409987820624
      ],
      [
        0.7255907688907874,
        1.8070059555170728,
        1.3622855163973069
      ]
    ],
    "head_box": [
      [
        -0.9792420473596238,
        0.8741488059224843,
        0.6684683437260039
      ],
      [
        0.9794888929356341,
        2.2,
        1.607709109430942
      ]
    ],
    "source_verified": true,
    "visual_review": {
      "status": "checked-front-side-quarter",
      "final_user_acceptance": "pending",
      "screenshots": "review/animal-materials-20261018/screenshots/pig-{view}-{version}.jpg",
      "remaining": "Original eye-surface dents/creases and small soft reflections remain; geometry not edited."
    },
    "vertices_normals_uvs_unchanged": true,
    "texture_images_unchanged": true,
    "cow_head_bake": {}
  },
  {
    "id": "alpaca",
    "name": "羊驼",
    "source": "public/models/animals/alpaca.glb",
    "source_sha256": "f53ef5bac7224c5665b457567b072d16d01aa738246cddc620e512c187e24531",
    "file": "public/models/animals-refined/v1/alpaca.glb",
    "url": "/models/animals-refined/v1/alpaca.glb",
    "bytes": 21936716,
    "version": "9ed13a58",
    "sha256": "9ed13a58a3373f24c17aba958c452f74332a6f7344dc39a52e0580687690d5b4",
    "roughness": 0.25,
    "normal_scale": 0.05,
    "specular": 0.18,
    "triangles": 358918,
    "eye_triangles": 2418,
    "eyes": [
      {
        "side": -1,
        "triangles": 1102,
        "depth": 0.008821832574903965,
        "center": [
          -0.1818130761384964,
          0.3704904019832611,
          0.5068355798721313
        ],
        "min": [
          -0.2264166623353958,
          0.3047856390476227,
          0.4810713231563568
        ],
        "max": [
          -0.12928499281406403,
          0.4370853006839752,
          0.5349213480949402
        ]
      },
      {
        "side": 1,
        "triangles": 1316,
        "depth": 0.01079344069585204,
        "center": [
          0.17098163068294525,
          0.3715943396091461,
          0.5108254551887512
        ],
        "min": [
          0.12659932672977448,
          0.3046630024909973,
          0.47999298572540283
        ],
        "max": [
          0.22454766929149628,
          0.4357849657535553,
          0.5366820693016052
        ]
      }
    ],
    "focus_box": [
      [
        -0.3536367637072761,
        1.3489265114582325,
        0.43945052010044294
      ],
      [
        0.35261950690944016,
        1.7100772296871067,
        0.6899365405238758
      ]
    ],
    "head_box": [
      [
        -0.5024659304096982,
        0.9689637867378663,
        0.11504749263336927
      ],
      [
        0.5024659304096982,
        2.2,
        0.8226556895418744
      ]
    ],
    "source_verified": true,
    "visual_review": {
      "status": "checked-front-side-quarter",
      "final_user_acceptance": "pending",
      "screenshots": "review/animal-materials-20261018/screenshots/alpaca-{view}-{version}.jpg",
      "remaining": "Original eye-surface dents/creases and small soft reflections remain; geometry not edited."
    },
    "vertices_normals_uvs_unchanged": true,
    "texture_images_unchanged": true,
    "cow_head_bake": {}
  },
  {
    "id": "hamster",
    "name": "仓鼠",
    "source": "public/models/animals/hamster.glb",
    "source_sha256": "90fe73a6bfb020010857d79e2fe77bf05f06f7d5a0e576cc18c83cfd4f1cf80b",
    "file": "public/models/animals-refined/v1/hamster.glb",
    "url": "/models/animals-refined/v1/hamster.glb",
    "bytes": 21451440,
    "version": "b34effc0",
    "sha256": "b34effc0a674bfc4768d41b2c1a506fd58737a67b6f7f65d80e076a2a99f5b7d",
    "roughness": 0.24,
    "normal_scale": 0.05,
    "specular": 0.18,
    "triangles": 189714,
    "eye_triangles": 5106,
    "eyes": [
      {
        "side": -1,
        "triangles": 2789,
        "depth": 0.019823176972568034,
        "center": [
          -0.2685590386390686,
          0.4146890938282013,
          0.6013506650924683
        ],
        "min": [
          -0.3614726960659027,
          0.28281936049461365,
          0.5563713312149048
        ],
        "max": [
          -0.1890956610441208,
          0.5002396702766418,
          0.6483883261680603
        ]
      },
      {
        "side": 1,
        "triangles": 2317,
        "depth": 0.017507393099367618,
        "center": [
          0.2505650520324707,
          0.4354577660560608,
          0.6026270985603333
        ],
        "min": [
          0.1892566680908203,
          0.28246769309043884,
          0.557041347026825
        ],
        "max": [
          0.3592216968536377,
          0.49834200739860535,
          0.6479013562202454
        ]
      }
    ],
    "focus_box": [
      [
        -0.5096384894011653,
        1.32308608821859,
        0.5272314258957241
      ],
      [
        0.5084224125030904,
        1.7829006403516832,
        0.8185568291683322
      ]
    ],
    "head_box": [
      [
        -0.813160471138386,
        0.9431238587642167,
        0.20282894872419802
      ],
      [
        0.8119443942403112,
        2.2,
        0.9645665366370221
      ]
    ],
    "source_verified": true,
    "visual_review": {
      "status": "checked-front-side-quarter",
      "final_user_acceptance": "pending",
      "screenshots": "review/animal-materials-20261018/screenshots/hamster-{view}-{version}.jpg",
      "remaining": "Original curled/dented pupil surface remains visible, especially front/quarter. No new painted catchlight was added."
    },
    "vertices_normals_uvs_unchanged": true,
    "texture_images_unchanged": true,
    "cow_head_bake": {}
  },
  {
    "id": "donkey",
    "name": "驴",
    "source": "public/models/animals/donkey.glb",
    "source_sha256": "a996c4cc70ca7bc35953fb9460420a21d8ce31580618d48ef6593951fe16d708",
    "file": "public/models/animals-refined/v1/donkey.glb",
    "url": "/models/animals-refined/v1/donkey.glb",
    "bytes": 22619872,
    "version": "d8a43102",
    "sha256": "d8a43102a4840d15636ba33ad1f3a6e4c29868a08b6005da657b39dab807527e",
    "roughness": 0.24,
    "normal_scale": 0.07,
    "specular": 0.2,
    "triangles": 212182,
    "eye_triangles": 2227,
    "eyes": [
      {
        "side": -1,
        "triangles": 923,
        "depth": 0.010607955418527125,
        "center": [
          -0.21122322976589203,
          0.1442393809556961,
          0.601702094078064
        ],
        "min": [
          -0.2683880031108856,
          0.057861000299453735,
          0.5747627019882202
        ],
        "max": [
          -0.15126998722553253,
          0.21016032993793488,
          0.6283153295516968
        ]
      },
      {
        "side": 1,
        "triangles": 1304,
        "depth": 0.01428157165646553,
        "center": [
          0.20017527043819427,
          0.14937320351600647,
          0.6027765274047852
        ],
        "min": [
          0.1504286676645279,
          0.05690532922744751,
          0.574742317199707
        ],
        "max": [
          0.27080535888671875,
          0.2159753292798996,
          0.6313266754150391
        ]
      }
    ],
    "focus_box": [
      [
        -0.41418159412288186,
        1.0614388322974666,
        0.565680137901082
      ],
      [
        0.41828605319893325,
        1.4651394687203272,
        0.8235479623539698
      ]
    ],
    "head_box": [
      [
        -0.4897556535043708,
        0.6845938659850148,
        0.2447412864428021
      ],
      [
        0.4897556535043708,
        2.0179844350327794,
        1.1041112732289375
      ]
    ],
    "source_verified": true,
    "visual_review": {
      "status": "checked-front-side-quarter",
      "final_user_acceptance": "pending",
      "screenshots": "review/animal-materials-20261018/screenshots/donkey-{view}-{version}.jpg",
      "remaining": "Original eye-surface dents/creases and small soft reflections remain; geometry not edited."
    },
    "vertices_normals_uvs_unchanged": true,
    "texture_images_unchanged": true,
    "cow_head_bake": {}
  },
  {
    "id": "capybara",
    "name": "普通水豚",
    "source": "public/models/animals/capybara.glb",
    "source_sha256": "702d16117595b807b190d7ebf8c9d033a4eed1c9965375d55ecb6a5fde426289",
    "file": "public/models/animals-refined/v1/capybara.glb",
    "url": "/models/animals-refined/v1/capybara.glb",
    "bytes": 17558400,
    "version": "916ca739",
    "sha256": "916ca7391821c8c97a88e801d57f50e284aa55b7633389707d280cc480af40f4",
    "roughness": 0.26,
    "normal_scale": 0.05,
    "specular": 0.18,
    "triangles": 134006,
    "eye_triangles": 5584,
    "eyes": [
      {
        "side": -1,
        "triangles": 2540,
        "depth": 0.025581302493810652,
        "center": [
          -0.25887084007263184,
          0.34788572788238525,
          0.4902561902999878
        ],
        "min": [
          -0.2809450328350067,
          0.293901652097702,
          0.45887231826782227
        ],
        "max": [
          -0.20149333775043488,
          0.41823533177375793,
          0.5493289828300476
        ]
      },
      {
        "side": 1,
        "triangles": 3044,
        "depth": 0.014035510085523128,
        "center": [
          0.24825693666934967,
          0.3474525213241577,
          0.5029016137123108
        ],
        "min": [
          0.20115065574645996,
          0.2930316627025604,
          0.45887601375579834
        ],
        "max": [
          0.280023992061615,
          0.41907432675361633,
          0.5560203194618225
        ]
      }
    ],
    "focus_box": [
      [
        -0.6435182893560181,
        1.4640155482308401,
        0.641603995977168
      ],
      [
        0.643648539962674,
        2.0104023580932022,
        1.100697751648545
      ]
    ],
    "head_box": [
      [
        -0.8410648533674581,
        1.14069514837773,
        0.3801368850292677
      ],
      [
        0.8410648533674581,
        2.2000001064138948,
        1.345578018217285
      ]
    ],
    "source_verified": true,
    "visual_review": {
      "status": "checked-front-side-quarter",
      "final_user_acceptance": "pending",
      "screenshots": "review/animal-materials-20261018/screenshots/capybara-{view}-{version}.jpg",
      "remaining": "Original eye-surface dents/creases and small soft reflections remain; geometry not edited."
    },
    "vertices_normals_uvs_unchanged": true,
    "texture_images_unchanged": true,
    "cow_head_bake": {}
  },
  {
    "id": "ostrich",
    "name": "鸵鸟",
    "source": "public/models/animals/ostrich.glb",
    "source_sha256": "bb48b9d95481d5157eda3218aa4e3b35aafe1baf7da62482847662caf1d3d702",
    "file": "public/models/animals-refined/v1/ostrich.glb",
    "url": "/models/animals-refined/v1/ostrich.glb",
    "bytes": 23794764,
    "version": "cfb9d34b",
    "sha256": "cfb9d34b6217401f30588514d844df9a37015ba98c3f52a46007e8ebe3facd26",
    "roughness": 0.23,
    "normal_scale": 0.06,
    "specular": 0.2,
    "triangles": 366294,
    "eye_triangles": 2128,
    "eyes": [
      {
        "side": -1,
        "triangles": 946,
        "depth": 0.013420128636062144,
        "center": [
          -0.15688660740852356,
          0.7696287035942078,
          0.49010971188545227
        ],
        "min": [
          -0.18705333769321442,
          0.7130133509635925,
          0.46477100253105164
        ],
        "max": [
          -0.10471933335065842,
          0.8360787034034729,
          0.5232513546943665
        ]
      },
      {
        "side": 1,
        "triangles": 1182,
        "depth": 0.01200254075229168,
        "center": [
          0.1392858624458313,
          0.7749985456466675,
          0.49806079268455505
        ],
        "min": [
          0.09909167140722275,
          0.7130339741706848,
          0.4634439945220947
        ],
        "max": [
          0.18561166524887085,
          0.8365943431854248,
          0.5244367122650146
        ]
      }
    ],
    "focus_box": [
      [
        -0.3081826334064203,
        1.8207859842994556,
        0.42099061126193726
      ],
      [
        0.3076985470596266,
        2.1717942518295907,
        0.6765081600518053
      ]
    ],
    "head_box": [
      [
        -0.5797242834678781,
        1.4408463335542212,
        0.09661322154501019
      ],
      [
        0.5797242834678781,
        2.2,
        0.8998798034528017
      ]
    ],
    "source_verified": true,
    "visual_review": {
      "status": "checked-front-side-quarter",
      "final_user_acceptance": "pending",
      "screenshots": "review/animal-materials-20261018/screenshots/ostrich-{view}-{version}.jpg",
      "remaining": "Original eye-surface dents/creases and small soft reflections remain; geometry not edited."
    },
    "vertices_normals_uvs_unchanged": true,
    "texture_images_unchanged": true,
    "cow_head_bake": {}
  },
  {
    "id": "pony",
    "name": "小马",
    "source": "public/models/animals/pony.glb",
    "source_sha256": "cc5c2361507be949227d3e0b0ffbd3a4b7380662babe73f0d70147d1687f1b76",
    "file": "public/models/animals-refined/v1/pony.glb",
    "url": "/models/animals-refined/v1/pony.glb",
    "bytes": 23706032,
    "version": "c3e7acc7",
    "sha256": "c3e7acc7dd2deae0d70191cdd28105820b019e6575bffb8382c87b0d4b0d1b9f",
    "roughness": 0.24,
    "normal_scale": 0.06,
    "specular": 0.2,
    "triangles": 356644,
    "eye_triangles": 1522,
    "eyes": [
      {
        "side": -1,
        "triangles": 642,
        "depth": 0.008252589218318462,
        "center": [
          -0.2320551872253418,
          0.29967227578163147,
          0.6130428910255432
        ],
        "min": [
          -0.27499398589134216,
          0.25244131684303284,
          0.5871216654777527
        ],
        "max": [
          -0.159401997923851,
          0.39703068137168884,
          0.6404502987861633
        ]
      },
      {
        "side": 1,
        "triangles": 880,
        "depth": 0.008,
        "center": [
          0.20098184049129486,
          0.3251006603240967,
          0.6233024001121521
        ],
        "min": [
          0.15634232759475708,
          0.2576773166656494,
          0.5941753387451172
        ],
        "max": [
          0.2652796506881714,
          0.3996393382549286,
          0.6422856450080872
        ]
      }
    ],
    "focus_box": [
      [
        -0.47170288987640036,
        1.3158080598842679,
        0.6487439727261942
      ],
      [
        0.45989837546003365,
        1.751092318551756,
        0.9349849864024561
      ]
    ],
    "head_box": [
      [
        -0.6010211746265488,
        0.9515385616490003,
        0.3417778635758968
      ],
      [
        0.6010211746265488,
        2.2000000792943784,
        1.2071646518926344
      ]
    ],
    "source_verified": true,
    "visual_review": {
      "status": "checked-front-side-quarter",
      "final_user_acceptance": "pending",
      "screenshots": "review/animal-materials-20261018/screenshots/pony-{view}-{version}.jpg",
      "remaining": "Original eye-surface dents/creases and small soft reflections remain; geometry not edited."
    },
    "vertices_normals_uvs_unchanged": true,
    "texture_images_unchanged": true,
    "cow_head_bake": {}
  },
  {
    "id": "goat",
    "name": "山羊",
    "source": "public/models/animals/goat.glb",
    "source_sha256": "dabb973ae91360bede2caac0b92542734517b3af301a5a511c8b331f4dcf4e9a",
    "file": "public/models/animals-refined/v1/goat.glb",
    "url": "/models/animals-refined/v1/goat.glb",
    "bytes": 24015652,
    "version": "da23daa5",
    "sha256": "da23daa5370388dd2f4fcad98ed7b24a973b0d2a0faadfc5d70cf4bd84e8b40e",
    "roughness": 0.24,
    "normal_scale": 0.06,
    "specular": 0.2,
    "triangles": 224368,
    "eye_triangles": 1718,
    "eyes": [
      {
        "side": -1,
        "triangles": 967,
        "depth": 0.013677121698856353,
        "center": [
          -0.25588709115982056,
          0.29826149344444275,
          0.6687533259391785
        ],
        "min": [
          -0.3049820065498352,
          0.2374650090932846,
          0.6261696815490723
        ],
        "max": [
          -0.18010999262332916,
          0.40462300181388855,
          0.7046893239021301
        ]
      },
      {
        "side": 1,
        "triangles": 751,
        "depth": 0.013068783655762672,
        "center": [
          0.2638823688030243,
          0.30160677433013916,
          0.661724865436554
        ],
        "min": [
          0.18367032706737518,
          0.23619334399700165,
          0.6201916337013245
        ],
        "max": [
          0.30514034628868103,
          0.4080580174922943,
          0.6999209523200989
        ]
      }
    ],
    "focus_box": [
      [
        -0.47576288635049896,
        1.2820546156638262,
        0.6437901458774956
      ],
      [
        0.4770983513575593,
        1.7174116820529504,
        0.9463035982436186
      ]
    ],
    "head_box": [
      [
        -0.7727800445518156,
        0.9094103126873452,
        0.3275186981258497
      ],
      [
        0.774115509558876,
        2.2,
        1.1765285941640153
      ]
    ],
    "source_verified": true,
    "visual_review": {
      "status": "checked-front-side-quarter",
      "final_user_acceptance": "pending",
      "screenshots": "review/animal-materials-20261018/screenshots/goat-{view}-{version}.jpg",
      "remaining": "Original eye-surface dents/creases and small soft reflections remain; geometry not edited."
    },
    "vertices_normals_uvs_unchanged": true,
    "texture_images_unchanged": true,
    "cow_head_bake": {}
  },
  {
    "id": "goose",
    "name": "白鹅",
    "source": "public/models/animals/goose.glb",
    "source_sha256": "7d3ca659d312414e32033f5970445adb9ffd8bdce0e4f4bd0cd5d64a61e5079c",
    "file": "public/models/animals-refined/v1/goose.glb",
    "url": "/models/animals-refined/v1/goose.glb",
    "bytes": 15091484,
    "version": "a3163d51",
    "sha256": "a3163d51628791583db4b69a752f6229ddef03933a041c888d109e53852a6995",
    "roughness": 0.23,
    "normal_scale": 0.06,
    "specular": 0.2,
    "triangles": 173960,
    "eye_triangles": 3254,
    "eyes": [
      {
        "side": -1,
        "triangles": 1571,
        "depth": 0.015589360892772674,
        "center": [
          -0.17079703509807587,
          0.7475773692131042,
          0.44159454107284546
        ],
        "min": [
          -0.2046923190355301,
          0.6833012700080872,
          0.4093259871006012
        ],
        "max": [
          -0.1156553328037262,
          0.8135249614715576,
          0.47914233803749084
        ]
      },
      {
        "side": 1,
        "triangles": 1683,
        "depth": 0.015289408527314662,
        "center": [
          0.15894679725170135,
          0.7503567337989807,
          0.44734781980514526
        ],
        "min": [
          0.11462533473968506,
          0.6834303736686707,
          0.41095399856567383
        ],
        "max": [
          0.20356599986553192,
          0.8148096203804016,
          0.4790383279323578
        ]
      }
    ],
    "focus_box": [
      [
        -0.32858915903271946,
        1.7865083276064375,
        0.35711393818961595
      ],
      [
        0.32839107525110117,
        2.1466523364169823,
        0.6228114124874944
      ]
    ],
    "head_box": [
      [
        -0.6320987950652427,
        1.4065599870698484,
        0.03272689314896174
      ],
      [
        0.6319007112836245,
        2.200000068910691,
        0.9054436395118869
      ]
    ],
    "source_verified": true,
    "visual_review": {
      "status": "checked-front-side-quarter",
      "final_user_acceptance": "pending",
      "screenshots": "review/animal-materials-20261018/screenshots/goose-{view}-{version}.jpg",
      "remaining": "Original eye-surface dents/creases and small soft reflections remain; geometry not edited."
    },
    "vertices_normals_uvs_unchanged": true,
    "texture_images_unchanged": true,
    "cow_head_bake": {}
  },
  {
    "id": "black-pig",
    "name": "黑猪",
    "source": "public/models/animals/black-pig.glb",
    "source_sha256": "7ab2a1dfda7c952ca7e7ff5b68728adfb2660f2ab52a65975d0ad4487a9b55a0",
    "file": "public/models/animals-refined/v1/black-pig.glb",
    "url": "/models/animals-refined/v1/black-pig.glb",
    "bytes": 14254068,
    "version": "2c483917",
    "sha256": "2c483917129c26355b6f5098ac2e3de84f6c5fa2771bf55c635989abf050cf63",
    "roughness": 0.25,
    "normal_scale": 0.06,
    "specular": 0.18,
    "triangles": 148108,
    "eye_triangles": 3515,
    "eyes": [
      {
        "side": -1,
        "triangles": 2066,
        "depth": 0.016339067742228507,
        "center": [
          -0.21333034336566925,
          0.2334691882133484,
          0.6826736330986023
        ],
        "min": [
          -0.3050103187561035,
          0.14738799631595612,
          0.6312583088874817
        ],
        "max": [
          -0.17494232952594757,
          0.29938364028930664,
          0.7102256417274475
        ]
      },
      {
        "side": 1,
        "triangles": 1449,
        "depth": 0.009892298001796007,
        "center": [
          0.21612393856048584,
          0.2305358499288559,
          0.6816387176513672
        ],
        "min": [
          0.17708967626094818,
          0.1473793387413025,
          0.6345073580741882
        ],
        "max": [
          0.303097665309906,
          0.2988276481628418,
          0.7052083015441895
        ]
      }
    ],
    "focus_box": [
      [
        -0.6948258792522822,
        1.2050787092799784,
        0.9601035848746086
      ],
      [
        0.6921684995368984,
        1.8045882958660961,
        1.391613677516468
      ]
    ],
    "head_box": [
      [
        -0.9463676095754515,
        0.8835942626664129,
        0.7006764219706468
      ],
      [
        0.9437102298600677,
        2.2000001076297986,
        1.6352699752588449
      ]
    ],
    "source_verified": true,
    "visual_review": {
      "status": "checked-front-side-quarter",
      "final_user_acceptance": "pending",
      "screenshots": "review/animal-materials-20261018/screenshots/black-pig-{view}-{version}.jpg",
      "remaining": "Original eye-surface dents/creases and small soft reflections remain; geometry not edited."
    },
    "vertices_normals_uvs_unchanged": true,
    "texture_images_unchanged": true,
    "cow_head_bake": {}
  },
  {
    "id": "deer",
    "name": "小鹿",
    "source": "public/models/animals/deer.glb",
    "source_sha256": "13e76d931c084a8e5fe0dd580ffa123771202b89695cd602772bd24602177547",
    "file": "public/models/animals-refined/v1/deer.glb",
    "url": "/models/animals-refined/v1/deer.glb",
    "bytes": 15976492,
    "version": "e7edefb9",
    "sha256": "e7edefb997c75a512d33067e2227d1cfb6a4445ba9ca9906e9f99b11f306df30",
    "roughness": 0.24,
    "normal_scale": 0.08,
    "specular": 0.22,
    "triangles": 165986,
    "eye_triangles": 1425,
    "eyes": [
      {
        "side": -1,
        "triangles": 619,
        "depth": 0.008,
        "center": [
          -0.1868300586938858,
          0.34999871253967285,
          0.6466022729873657
        ],
        "min": [
          -0.23170900344848633,
          0.29401999711990356,
          0.6163956522941589
        ],
        "max": [
          -0.13770633935928345,
          0.4510743319988251,
          0.6697260737419128
        ]
      },
      {
        "side": 1,
        "triangles": 806,
        "depth": 0.009568123333156108,
        "center": [
          0.18663690984249115,
          0.3493116497993469,
          0.6460756659507751
        ],
        "min": [
          0.13447965681552887,
          0.2928283214569092,
          0.6132813096046448
        ],
        "max": [
          0.23289066553115845,
          0.4507347047328949,
          0.6724665760993958
        ]
      }
    ],
    "focus_box": [
      [
        -0.3600103431991483,
        1.3353056265053733,
        0.5938817412820686
      ],
      [
        0.3621396396413329,
        1.7263790817759141,
        0.8472994811547887
      ]
    ],
    "head_box": [
      [
        -0.6456736555213117,
        0.9553618751451104,
        0.26949979532622065
      ],
      [
        0.6456736555213117,
        2.1999999310862695,
        0.9813278685998096
      ]
    ],
    "source_verified": true,
    "visual_review": {
      "status": "checked-front-side-quarter",
      "final_user_acceptance": "pending",
      "screenshots": "review/animal-materials-20261018/screenshots/deer-{view}-{version}.jpg",
      "remaining": "Original eye-surface dents/creases and small soft reflections remain; geometry not edited."
    },
    "vertices_normals_uvs_unchanged": true,
    "texture_images_unchanged": true,
    "cow_head_bake": {}
  }
];
