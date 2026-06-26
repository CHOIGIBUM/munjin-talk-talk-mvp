import { useEffect, useState } from 'react'
import { Link, useLocation, useNavigate, useParams } from 'react-router-dom'
import PatientFlow from './PatientFlow.jsx'
import { getIntakeSession, requestStaffHelp } from '../../services/api.js'
import './PatientKioskView.css'

// 접수처에서 만든 sessionId를 받아 실제 환자 태블릿 문진을 시작하는 화면입니다.
// 모든 답변 저장과 상태 변경은 백엔드 API를 통해 DynamoDB 세션에 반영됩니다.
export default function PatientKioskView() {
  const { sessionId } = useParams()
  const location = useLocation()
  const navigate = useNavigate()
  const [session, setSession] = useState(null)
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState('')

  // URL의 sessionId로 환자 정보와 초진/재진 설정을 불러옵니다.
  useEffect(() => {
    let active = true
    setLoading(true)
    setLoadError('')
    const params = new URLSearchParams(location.search)
    const patientToken = params.get('pt') || params.get('patient_token') || ''

    loadPatientSession(sessionId, patientToken).then((next) => {
      if (active) {
        setSession(next)
        setLoadError('')
      }
    }).catch((error) => {
      console.error('patient session load failed:', error)
      if (active) {
        setSession(null)
        setLoadError(error?.message || '')
      }
    }).finally(() => {
      if (active) setLoading(false)
    })
    return () => {
      active = false
    }
  }, [sessionId, location.search])

  if (loading) {
    return (
      <div className="kiosk-missing">
        <h1>문진 세션을 불러오는 중입니다</h1>
      </div>
    )
  }

  if (!session) {
    return (
      <div className="kiosk-missing">
        <h1>문진 세션을 찾을 수 없습니다</h1>
        <p>{loadError || '접수 데스크에서 환자 확인 후 새 문진 세션을 생성해 주세요.'}</p>
        <Link to="/staff">접수 화면으로 이동</Link>
      </div>
    )
  }

  return (
    <PatientFlow
      sessionId={session.sessionId}
      patient={session.patient}
      queueNumber={session.queueNumber}
      doctorQueuePosition={session.doctorQueuePosition}
      questionSetId={session.questionSetId}
      initialVisitType={session.visitType}
      frameVariant="device"
      skipVisitTypeWhenPreset={false}
      onStaffCallRequest={() => {
        requestStaffHelp(session.sessionId).catch((error) => {
          console.warn('staff call request failed:', error)
        })
      }}
      onExitToQueue={() => navigate('/patient')}
    />
  )
}

async function loadPatientSession(sessionId, patientToken) {
  try {
    return await getIntakeSession(sessionId, { patientToken, throwOnError: true })
  } catch (error) {
    if (patientToken || ![401, 403].includes(Number(error?.status))) throw error
    return getIntakeSession(sessionId, { role: 'staff', throwOnError: true })
  }
}
