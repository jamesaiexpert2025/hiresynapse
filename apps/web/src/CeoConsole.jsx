import React, { useEffect, useState } from 'react'
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

export default function CeoConsole(){
  const [ideas, setIdeas] = useState([])
  const [title, setTitle] = useState('')
  const [desc, setDesc] = useState('')
  const [files, setFiles] = useState('')

  const load = async()=>{
    try{
      const data = await api('/agent/list')
      setIdeas(data || [])
    } catch(e){
      console.error(e)
      alert('Load failed: ' + e.message)
    }
  }
  useEffect(()=>{ load() }, [])

  const propose = async()=>{
    try{
      await api('/agent/propose', { method:'POST', body:{ title, description:desc }})
      setTitle(''); setDesc('')
      await load()
    } catch(e){ alert('Propose failed: ' + e.message) }
  }

  const approve = async(id)=>{
    try{
      await api(`/agent/approve/${id}`, { method:'POST' })
      await load()
    } catch(e){ alert('Approve failed: ' + e.message) }
  }

  const execute = async(id)=>{
    try{
      const parsed = files ? JSON.parse(files) : []
      const r = await api('/agent/execute', { method:'POST', body:{ idea_id:id, files:parsed, message:`Implement idea ${id}` }})
      alert('PR opened: ' + (r.pr_url || 'OK'))
      await load()
    } catch(e){ alert('Execute failed: ' + e.message) }
  }

  return (
    <div style={{border:'1px solid #ddd', padding:16, borderRadius:8}}>
      <h3>CEO Console</h3>
      <div style={{border:'1px dashed #ccc', padding:12, borderRadius:8, marginBottom:12}}>
        <div style={{fontWeight:600, marginBottom:8}}>Propose New Idea</div>
        <input placeholder="Title" value={title} onChange={e=>setTitle(e.target.value)} style={{width:'100%', padding:8, marginBottom:8}}/>
        <textarea placeholder="Describe the idea/plan" value={desc} onChange={e=>setDesc(e.target.value)} style={{width:'100%', minHeight:80, padding:8, marginBottom:8}}/>
        <div style={{fontSize:12, color:'#666', marginBottom:6}}>Optional: JSON list of files to change (path + content). Example:</div>
        <textarea placeholder='[{"path":"apps/web/src/NewBadge.jsx","content":"export default()=> <span>Hi</span>"}]' value={files} onChange={e=>setFiles(e.target.value)} style={{width:'100%', minHeight:80, padding:8, marginBottom:8}}/>
        <button onClick={propose}>Propose</button>
      </div>

      <div style={{display:'grid', gap:12}}>
        {ideas.map(i => (
          <div key={i.id} style={{border:'1px solid #eee', padding:12, borderRadius:8}}>
            <div style={{fontWeight:600}}>#{i.id} {i.title} — <span style={{fontSize:12, color:'#555'}}>{i.status}</span></div>
            <div style={{fontSize:14, color:'#555', margin:'6px 0'}}>{i.description}</div>
            <div style={{display:'flex', gap:8}}>
              <button onClick={()=>approve(i.id)}>Approve (Admin)</button>
              <button onClick={()=>execute(i.id)}>Execute (AI CEO)</button>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
