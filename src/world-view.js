import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

export class WorldView {
  constructor(host) {
    this.host = host;
    this.scene = new THREE.Scene();
    this.scene.background = new THREE.Color('#101820');
    this.scene.fog = new THREE.Fog('#101820', 14, 28);
    this.camera = new THREE.PerspectiveCamera(42, 1, .1, 100);
    this.camera.position.set(8, 8, 11);
    this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false });
    this.renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
    this.renderer.shadowMap.enabled = true;
    this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    this.renderer.outputColorSpace = THREE.SRGBColorSpace;
    host.appendChild(this.renderer.domElement);
    this.controls = new OrbitControls(this.camera, this.renderer.domElement);
    this.controls.target.set(0, .5, 0); this.controls.maxPolarAngle = Math.PI * .48;
    this.setupScene(); this.resize();
    window.addEventListener('resize', () => this.resize());
  }

  setupScene() {
    this.ambient = new THREE.HemisphereLight('#c7d5e3', '#29343a', 1.3); this.scene.add(this.ambient);
    this.sun = new THREE.DirectionalLight('#fff0ce', 2.3); this.sun.position.set(-4, 8, 3); this.sun.castShadow = true;
    this.sun.shadow.mapSize.set(1024,1024); this.scene.add(this.sun);
    const floor = new THREE.Mesh(new THREE.PlaneGeometry(10, 7), new THREE.MeshStandardMaterial({ color:'#263238', roughness:.88 }));
    floor.rotation.x = -Math.PI/2; floor.receiveShadow = true; this.scene.add(floor);
    const grid = new THREE.GridHelper(10, 20, '#46545a', '#344147'); grid.position.y = .012; this.scene.add(grid);
    const wallMat = new THREE.MeshStandardMaterial({ color:'#1b292e', roughness:1, side:THREE.DoubleSide });
    for (const [x,z,sx,sz] of [[0,-3.5,10,.12],[-5,0,.12,7],[5,0,.12,7]]) {
      const wall = new THREE.Mesh(new THREE.BoxGeometry(sx,2.3,sz), wallMat); wall.position.set(x,1.15,z); wall.receiveShadow=true; this.scene.add(wall);
    }
    this.objectMeshes = new Map();
    this.agent = new THREE.Group();
    const body = new THREE.Mesh(new THREE.CapsuleGeometry(.25,.55,5,10), new THREE.MeshStandardMaterial({ color:'#d7e5e8', roughness:.52 })); body.position.y=.56; body.castShadow=true; this.agent.add(body);
    const head = new THREE.Mesh(new THREE.SphereGeometry(.23,20,16), new THREE.MeshStandardMaterial({color:'#a9c9cb',roughness:.45})); head.position.y=1.02; head.castShadow=true; this.agent.add(head);
    const eye = new THREE.Mesh(new THREE.SphereGeometry(.035,10,8), new THREE.MeshBasicMaterial({color:'#18282d'})); eye.position.set(0,1.04,.205); this.agent.add(eye);
    this.scene.add(this.agent);
  }

  setAgentPose(pose) { this.agent.position.set(pose.x,0,pose.z); this.agent.rotation.y=pose.heading; }
  setObjects(objects) {
    for (const o of objects) {
      let mesh=this.objectMeshes.get(o.id);
      if (!mesh) {
        const geo=o.type==='box'?new THREE.BoxGeometry(.8,.8,.8):o.type==='cylinder'?new THREE.CylinderGeometry(.36,.36,.9,24):new THREE.SphereGeometry(o.radius,24,18);
        mesh=new THREE.Mesh(geo,new THREE.MeshStandardMaterial({color:o.color,roughness:.55})); mesh.castShadow=true; mesh.receiveShadow=true; this.scene.add(mesh); this.objectMeshes.set(o.id,mesh);
      }
      mesh.position.set(o.x,o.y,o.z);
    }
  }
  update(dt, worldTime) {
    const hour=(6+worldTime/120*24)%24;
    const daylight=Math.max(.12,Math.sin((hour-6)/12*Math.PI));
    this.sun.intensity=.25+2.1*daylight; this.ambient.intensity=.45+.85*daylight;
    this.sun.color.setHSL(.12,.32,.72+.2*daylight);
    this.renderer.render(this.scene,this.camera); this.controls.update();
  }
  resize() { const w=this.host.clientWidth,h=this.host.clientHeight; if(!w||!h)return; this.camera.aspect=w/h; this.camera.updateProjectionMatrix(); this.renderer.setSize(w,h); }
}
