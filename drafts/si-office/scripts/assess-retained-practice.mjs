import {readFileSync} from 'node:fs';
export function assessRetainedPractice(receipt,program){
 if(receipt.mode!=='SYNTHETIC ADVANCED PRACTICE / NOT ASSESSED'||!Array.isArray(receipt.results))throw Error('RECEIPT_REQUIRED');
 const rows=[];
 for(const team of receipt.results){if(team.reviewedAdvancedDrafts!==program.advanced.length)throw Error('COHORT_COUNT_MISMATCH');
  for(const track of program.advanced){const retained=team.taskEvidence?.find(t=>t.track===track.key);
   rows.push({workspace:team.workspace,track:track.key,taskKey:retained?.taskKey??null,expectedEvidence:track.expectedEvidence,retainedTaskEvidence:!!retained,workflow:'REPORTED REVIEWED DRAFT',assessment:'NOT ASSESSED',competencyPass:false,findings:retained?['Reflection draft does not execute all curriculum steps','Prerequisites and assessor authority unverified']:['Historical per-task output/taskKey not retained','Reflection draft does not execute all curriculum steps','Prerequisites and assessor authority unverified']});
  }
 }
 return {scope:'EVIDENCE SUFFICIENCY REVIEW, NOT COMPETENCY CERTIFICATION',taskSlots:rows.length,competencyPass:0,notAssessed:rows.length,rows};
}
if(process.argv[1]?.endsWith('/assess-retained-practice.mjs'))console.log(JSON.stringify(assessRetainedPractice(JSON.parse(readFileSync(process.argv[2])),JSON.parse(readFileSync(new URL('../configs/training-basic-v1.json',import.meta.url)))),null,2));
