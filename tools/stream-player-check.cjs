// Scheduler checks with a controlled audio clock, using the actual TypeScript player.
const fs=require('fs'),assert=require('assert'),Module=require('module');
const ts=require('../frontend/node_modules/typescript');
let clock;
global.AudioContext=class {
  constructor(){this.currentTime=0;this.state='running';this.destination={};this.created=[];clock=this;}
  resume(){return Promise.resolve();}
  createGain(){return {gain:{value:1},connect(){},disconnect(){}};}
  createBufferSource(){const node={buffer:null,playbackRate:{value:1},onended:null,connect(){},disconnect(){},stop(){this.stopped=true;},start(at,offset){this.at=at;this.offset=offset;}};this.created.push(node);return node;}
  decodeAudioData(){return Promise.resolve({duration:1.2});}
  advance(seconds){this.currentTime+=seconds;for(const node of this.created)if(!node.stopped&&!node.ended&&node.at!==undefined&&node.at+(node.buffer.duration-node.offset)/node.playbackRate.value<=this.currentTime){node.ended=true;node.onended?.();}}
};
global.fetch=async()=>({ok:true,arrayBuffer:async()=>new ArrayBuffer(8)});
const file=require('path').resolve('frontend/src/stream-player.ts');
const compiled=ts.transpileModule(fs.readFileSync(file,'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022}}).outputText;
const moduleObject=new Module(file,module);moduleObject.filename=file;moduleObject.paths=module.paths;moduleObject._compile(compiled,file);
const {StreamPlayer}=moduleObject.exports;
const delay=ms=>new Promise(resolve=>setTimeout(resolve,ms));
(async()=>{
  let state; const errors=[];
  const player=new StreamPlayer('a'.repeat(32),0,value=>state=value,error=>errors.push(error));
  player.preferences('smooth',1,.8);player.play(true);
  player.update({id:'a'.repeat(32),state:'generating',running:true,complete:false,total:80,available:56,throughput:2,sections:Array.from({length:40},(_,index)=>({index,start:index*1.4,duration:1.2,pause:.2}))});
  await delay(250);
  assert(state.playing,'Fewer interruptions never began with many short sections');
  const starts=clock.created.filter(n=>n.at!==undefined);
  assert(starts.length>16,'Buffer was capped below the requested listening target');
  for(let i=1;i<starts.length;i++)assert(Math.abs(starts[i].at-starts[i-1].at-1.4)<1e-6,'Section order/pause timing drifted');
  clock.advance(20);await delay(130);
  assert(player.nodes.size<30,'Ended sources retained decoded buffers');
  player.pause();const paused=state.position;
  clock.advance(10);await delay(130);assert(Math.abs(state.position-paused)<.001,'Paused position moved');
  player.seek(2.5);player.preferences('sooner',1.25,.4);player.play();await delay(130);
  const current=clock.created.filter(n=>n.at!==undefined&&!n.stopped&&!n.ended);
  assert(Math.abs(current[0].offset-1.1)<1e-6,'Seek skipped or repeated speech inside a section');
  assert(current[0].playbackRate.value===1.25);
  assert(Math.abs(current[1].at-current[0].at-.3/1.25)<1e-6,'Playback rate changed pause alignment');
  player.dispose();assert(player.nodes.size===0&&player.buffers.size===0);assert.deepEqual(errors,[]);
  console.log(JSON.stringify({success:true,manyShortSections:true,orderedPauses:true,boundedSources:true,seekRateAlignment:true}));
})().catch(e=>{console.error(e);process.exit(1)});
