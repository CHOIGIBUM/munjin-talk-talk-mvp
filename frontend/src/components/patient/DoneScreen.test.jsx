import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import DoneScreen from './DoneScreen.jsx'

const patient = { name: '홍*동', honorific: '어르신', queueNumber: 7 }

describe('DoneScreen', () => {
  it('일반 완료 메시지를 렌더링', () => {
    render(<DoneScreen patient={patient} visitType="initial" queueNumber={7} />)
    expect(screen.getByText(/문진이/)).toBeInTheDocument()
    expect(screen.getByText(/모두 끝났어요/)).toBeInTheDocument()
  })

  it('대기 순번을 표시', () => {
    render(<DoneScreen patient={patient} visitType="initial" queueNumber={7} />)
    expect(screen.getByText('대기 순번')).toBeInTheDocument()
    expect(screen.getByText('7')).toBeInTheDocument()
  })

  it('직원 인계(stopped) 시 다른 메시지', () => {
    render(<DoneScreen patient={patient} visitType="initial" stopped={true} queueNumber={7} />)
    expect(screen.getByText(/직원이/)).toBeInTheDocument()
    expect(screen.getByText(/도와드릴게요/)).toBeInTheDocument()
  })

  it('순번이 없으면 — 표시', () => {
    render(<DoneScreen patient={{ name: '홍*동', honorific: '어르신' }} visitType="initial" queueNumber={0} />)
    expect(screen.getByText('—')).toBeInTheDocument()
  })

  it('onExitToQueue 콜백이 있으면 버튼 렌더 & 클릭 동작', () => {
    const onExit = vi.fn()
    render(<DoneScreen patient={patient} visitType="initial" queueNumber={7} onExitToQueue={onExit} />)
    const btn = screen.getByText(/다음 환자 선택 화면/)
    fireEvent.click(btn)
    expect(onExit).toHaveBeenCalledOnce()
  })

  it('onExitToQueue 없으면 버튼 없음', () => {
    render(<DoneScreen patient={patient} visitType="initial" queueNumber={7} />)
    expect(screen.queryByText(/다음 환자 선택 화면/)).not.toBeInTheDocument()
  })
})
