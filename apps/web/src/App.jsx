import React, { useState } from 'react'
import CeoConsole from './CeoConsole.jsx'

const API = import.meta.env.VITE_API_URL

async function api(path, opts={}){
  const token = localStorage.getItem('hs_token') || ''
  const res = await fetch(`${API}${path}`, {
    method: opts.method||'GET',
    headers: { 'Content-Type':'application/json', ...(token?{Authorization:`Bearer ${token}`}:{}) },
    body: opts.body?JSON.stringify(opts.body):undefined
  })
  if(!res.ok){
    throw new Error(await res.text())
  }
  return res.json()
}

function AuthPanel({ onAuth }){
  const [email, setEmail] = useState('admin@hiresynapse.ai')
  const [password, setPassword] = useState('admin123')
  const [busy, setBusy] = useState(false)

  const login = async ()=>{
    setBusy(true)
    try {
      const res = await fetch(`${API}/auth/token`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: new URLSearchParams({ username: email, password })
      })
      if(!res.ok) throw new Error(await res.text())
      const data = await res.json()
      localStorage.setItem('hs_token', data.access_token)
      onAuth(true)
    } catch(e){
      alert('Login failed: ' + e.message)
    } finally {
      setBusy(false)
    }
  }

  const logout = ()=>{
    localStorage.removeItem('hs_token')
    onAuth(false)
  }

  const authed = !!localStorage.getItem('hs_token')
  return (
    <div style={{border:'1px solid #ddd', padding:16, borderRadius:8}}>
      <h3>Authentication</h3>
      {authed ? (
        <div style={{display:'flex', gap:8, alignItems:'center'}}>
          <span>Signed in.</span>
          <button onClick={logout}>Sign out</button>
        </div>
      ) : (
        <div style={{display:'grid', gap:8, maxWidth:420}}>
          <input placeholder="Email" value={email} onChange={e=>setEmail(e.target.value)} />
          <input placeholder="Password" type="password" value={password} onChange={e=>setPassword(e.target.value)} />
          <button onClick={login} disabled={busy}>{busy?'Signing in…':'Sign in'}</button>
          <div style={{fontSize:12, color:'#666'}}>Tip: use your Admin or AI CEO credentials you set in Render.</div>
        </div>
      )}
    </div>
  )
}

export default function App(){
  const [authed, setAuthed] = useState(!!localStorage.getItem('hs_token'))
  return (
    <div style={{maxWidth:900, margin:'40px auto', padding:'0 16px', fontFamily:'Inter, system-ui, Arial'}}>
      <h1>HireSynapse — Agentic AI CEO</h1>
      <p>This simple console lets you log in and work with the Agentic AI CEO (propose → approve → execute → preview).</p>
      <AuthPanel onAuth={setAuthed} />
      <div style={{height:16}}/>
      {authed ? <CeoConsole/> : <div style={{color:'#a66'}}>Please sign in to continue.</div>}
    </div>
  )
}
