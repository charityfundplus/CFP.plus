import {trainingWorksheet} from './training-export-worksheet.mjs';
import {readFileSync} from 'node:fs';
import {fileURLToPath} from 'node:url';

// Combines existing selected-pair exports for one learner without changing Core state.
// A selected-pair export cannot by itself cover exercises assigned to other pairs.
export function trainingEvidencePack(envelopes, program, {subject, developmentRevision, allowedPairs}) {
  if (typeof subject !== 'string' || !subject.trim() || !Array.isArray(envelopes)
      || !Array.isArray(allowedPairs) || !allowedPairs.length || !/^[a-f0-9]{40}$/.test(developmentRevision || ''))
    throw Error('PACK_SCOPE_REQUIRED');
  const requiredPairs = [...new Set(program.exercises.map(e=>e.pairTemplate))];
  if (requiredPairs.some(pair=>!allowedPairs.includes(pair))) throw Error('PROGRAM_PAIR_OUTSIDE_SCOPE');
  const worksheets = new Map(), exerciseKeys = new Set();
  for (const exercise of program.exercises) {
    if (exerciseKeys.has(exercise.localKey)) throw Error('PROGRAM_EXERCISE_DUPLICATE');
    exerciseKeys.add(exercise.localKey);
  }
  for (const envelope of envelopes) {
    // Validate the envelope and task scopes before reading its subject/pair.
    const complete = trainingWorksheet(envelope,program,{developmentRevision,allowedPairs});
    if (complete.subject !== subject || !requiredPairs.includes(complete.pairKey)) throw Error('EXPORT_SUBJECT_OR_PAIR_OUTSIDE_SCOPE');
    if (worksheets.has(complete.pairKey)) throw Error('DUPLICATE_PAIR_EXPORT');
    const p = JSON.parse(envelope.payloadJSON);
    const keys = new Set(), tasks = new Set();
    for (const mapping of p.journey.exercises || []) {
      const key = mapping.exercise || mapping.localKey || mapping.exerciseKey || mapping.key;
      const exercise = program.exercises.find(row=>row.localKey===key);
      if (!exercise || exercise.pairTemplate !== complete.pairKey || keys.has(key)
          || (mapping.taskKey && tasks.has(mapping.taskKey))) throw Error('EXERCISE_PAIR_OR_DUPLICATE_BINDING');
      keys.add(key);if(mapping.taskKey)tasks.add(mapping.taskKey);
    }
    worksheets.set(complete.pairKey,complete);
  }
  const exercises = program.exercises.map(exercise=>{
    const w=worksheets.get(exercise.pairTemplate), row=w?.exercises.find(e=>e.localKey===exercise.localKey);
    return {localKey:exercise.localKey,pairKey:exercise.pairTemplate,taskKey:row?.taskKey || null,
      outputSha256:row?.outputSha256 || null,inputSha256:w?.inputSha256 || null,
      basicDraftEvidenceReady:row?.basicDraftEvidenceReady === true && !!row?.outputSha256,
      assessment:'NOT ASSESSED',competencyPass:false};
  });
  const lessons = requiredPairs.map(pairKey=>({pairKey,acknowledged:worksheets.get(pairKey)?.lessons.every(l=>l.acknowledged) === true}));
  return {schemaVersion:1,mode:'READ_ONLY MULTI-PAIR VI/EN TRAINING PACK',subject,developmentRevision,
    evaluationBaseline:'b75b780eb64430355f0b51a4b58b9e5269e0db43',sourceRevisionVerified:false,
    missingPairs:requiredPairs.filter(pair=>!worksheets.has(pair)),lessons,exercises,
    basicDraftEvidenceReady:lessons.every(l=>l.acknowledged)&&exercises.every(e=>e.basicDraftEvidenceReady),
    findings:['REVISION_REQUIRES_BUILD_MANIFEST_READBACK','REAL_REVIEWER_AUTHORITY_PENDING'],
    pairEvidence:[...worksheets.values()].map(w=>({pairKey:w.pairKey,inputSha256:w.inputSha256,
      sourceRevisionClaim:w.sourceRevisionClaim,sourceRevisionVerified:false,
      declarations:w.declarations,hstdn:w.hstdn,findings:w.findings})),
    advanced:program.advanced.map(track=>({key:track.key,assessment:'NOT ASSESSED',competencyPass:false})),
    labels:{vi:'Gói bằng chứng nhiều pair; không chứng nhận năng lực',en:'Evidence across pairs; no competency certification'},
    coreStateChanged:false,privilegeChange:false,activationAllowed:false,providerCalls:0};
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  try {
    const [input,subject,developmentRevision]=process.argv.slice(2);
    const program=JSON.parse(readFileSync(new URL('../configs/training-basic-v1.json',import.meta.url),'utf8'));
    const pairs=JSON.parse(readFileSync(new URL('../configs/pairs.json',import.meta.url),'utf8'));
    console.log(JSON.stringify(trainingEvidencePack(JSON.parse(readFileSync(input,'utf8')),program,
      {subject,developmentRevision,allowedPairs:pairs.map(p=>p.key)}),null,2));
  } catch(error) { console.error(error.message);process.exitCode=1; }
}
