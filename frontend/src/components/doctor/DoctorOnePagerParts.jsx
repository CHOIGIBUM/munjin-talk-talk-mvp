// DoctorOnePager에서 반복 사용되는 작은 UI 부품과 단서 연결 규칙입니다.
// 큰 화면 컴포넌트가 레이아웃에만 집중하도록 이 파일로 분리했습니다.

export const CopyIcon = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
    <rect x="8" y="8" width="12" height="12" rx="2" stroke="currentColor" strokeWidth="2"/>
    <path d="M16 8V6a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v8a2 2 0 0 0 2 2h2" stroke="currentColor" strokeWidth="2"/>
  </svg>
)

export const CheckIcon = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
    <path d="M5 12l5 5L20 7" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"/>
  </svg>
)

const SYMPTOM_CONTEXT_CATEGORIES = ['증상맥락', '재진경과']
const STANDALONE_CONTEXT_CATEGORIES = ['증상맥락', '재진경과', '복약정보', '복약순응도', '약물반응']

function clueTextKey(text) {
  return String(text || '').replace(/[^0-9A-Za-z가-힣]+/g, '')
}

export function clueKey(clue) {
  return clue.id || `${clue.category || ''}-${clue.source_question || ''}-${clue.source_quote || clue.summary || ''}`
}

export function getCluesForSlot(slot, clues = []) {
  return (clues || []).filter((clue) => {
    const relatedSymptoms = clue.related_symptoms || []
    const slotNames = [slot.name, slot.normalizedText]
      .map(clueTextKey)
      .filter(Boolean)
    const sameSymptom = relatedSymptoms.some((name) => {
      const related = clueTextKey(name)
      return related && slotNames.some((slotName) => slotName.includes(related) || related.includes(slotName))
    })
    const clueQuote = clue.source_quote || clue.summary || ''
    const slotQuote = slot.sourceQuote || slot.normalizedText || ''
    const sameQuote = Boolean(clueQuote && slotQuote && (slotQuote.includes(clueQuote) || clueQuote.includes(slotQuote)))
    const isSymptomContext = SYMPTOM_CONTEXT_CATEGORIES.includes(clue.category)
    // 같은 질문에서 나온 단서라는 이유만으로 증상 카드에 붙이지 않습니다.
    // 예: "목 통증은 어제부터" 단서가 같은 Q1의 콧물/가래 카드까지 번지는 것을 막습니다.
    return isSymptomContext && (sameQuote || sameSymptom)
  }).slice(0, 4)
}

// 특정 증상 카드에 붙지 않은 복약/경과/문진 맥락은 별도 맥락 chip으로 보여줍니다.
export function getUnlinkedClues(slots = [], clues = []) {
  const linkedKeys = new Set()

  ;(slots || []).forEach((slot) => {
    getCluesForSlot(slot, clues).forEach((clue) => linkedKeys.add(clueKey(clue)))
  })

  return (clues || []).filter((clue) => {
    if (linkedKeys.has(clueKey(clue))) return false
    return STANDALONE_CONTEXT_CATEGORIES.includes(clue.category)
  }).slice(0, 8)
}

export function ClueChip({ clue }) {
  const isPriority = clue.priority === '우선'
  const summary = clue.summary || ''
  const quote = clue.source_quote || ''
  const text = summary || quote
  const showQuote = Boolean(quote && quote !== summary)
  if (!text) return null

  return (
    <span className={`slot-clue-chip ${isPriority ? 'priority' : ''}`}>
      <b>{clue.label || clue.category}</b>
      <span>{text}</span>
      {showQuote && <small>원문 "{quote}"</small>}
    </span>
  )
}
