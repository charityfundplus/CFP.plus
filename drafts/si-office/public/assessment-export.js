// Display/export only. Authorization stays server-side; no competency promotion.
export function scopedAssessmentEvidence(state,subject,pairKey){
 if(!state?.auth||subject!==state.auth.id)throw Error('ASSESSMENT_EXPORT_SUBJECT_DENIED');
 return structuredClone((state.learning?.assessments||[]).filter(r=>r.subject===subject&&r.pairKey===pairKey));
}
