// 위험 키워드 - 클라이언트 측 1차 감지 (백엔드에서 정밀 판별 별도)
// 감지되면 일반 검증 화면 대신 SafetyAlertScreen으로 분기

// 클라이언트 1차 안전 감지 키워드입니다.
// 의료진 호출을 빠르게 띄우기 위한 규칙이며, 진단이나 최종 분류를 대신하지 않습니다.
// STT는 띄어쓰기와 조사가 흔들리기 때문에 공백/문장부호를 제거한 문장도 함께 확인합니다.
export const SAFETY_KEYWORDS = [
  {
    label: '객혈 의심',
    category: 'hemoptysis',
    severity: 'high',
    terms: [
      '객혈',
      '각혈',
      '피가 섞',
      '피 섞',
      '피섞',
      '피가래',
      '피 섞인 가래',
      '가래에 피',
      '피를 토',
      '피 토',
      '피가 나왔',
      '피나왔',
    ],
  },
  {
    label: '토혈 의심',
    category: 'hematemesis',
    severity: 'high',
    terms: ['토혈', '피를 토', '피 토', '피토'],
  },
  {
    label: '호흡곤란 의심',
    category: 'dyspnea',
    severity: 'high',
    terms: [
      '숨을 못 쉬',
      '숨 못 쉬',
      '숨못쉬',
      '숨이 막',
      '숨막',
      '숨이 너무 차',
      '숨이 많이 차',
      '숨쉬기 힘',
      '숨 쉬기 힘',
      '말을 못 하',
      '숨이 차서 말',
    ],
  },
  {
    label: '의식 저하 의심',
    category: 'consciousness',
    severity: 'high',
    terms: ['쓰러졌', '쓰러지', '기절', '의식이 없', '의식 없', '정신을 잃'],
  },
  {
    label: '흉통 의심',
    category: 'chest_pain',
    severity: 'high',
    terms: [
      '흉통',
      '가슴이 너무 아',
      '가슴이 아',
      '가슴 아',
      '가슴이 답답',
      '가슴 답답',
      '가슴을 쥐어',
      '가슴 조여',
      '심장이 조여',
    ],
  },
]

function normalizeSafetyText(value) {
  return String(value || '')
    .toLowerCase()
    .replace(/[\s"'“”‘’.,!?…·\-_/\\()[\]{}:;]/g, '')
}

/**
 * 텍스트에서 위험 키워드를 찾아 반환
 * @param {string} text - 전사 텍스트
 * @returns {{keyword, category, severity, position} | null}
 */
export function detectSafetyKeyword(text) {
  if (!text) return null
  const rawText = String(text)
  const compactText = normalizeSafetyText(rawText)

  for (const item of SAFETY_KEYWORDS) {
    for (const term of item.terms) {
      const rawIndex = rawText.indexOf(term)
      const compactTerm = normalizeSafetyText(term)
      if (rawIndex >= 0 || (compactTerm && compactText.includes(compactTerm))) {
        return {
          label: item.label,
          category: item.category,
          severity: item.severity,
          keyword: term,
          matched: term,
          position: rawIndex >= 0 ? rawIndex : 0,
        }
      }
    }
  }
  return null
}
