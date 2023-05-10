import { createClient } from '@supabase/supabase-js'

const supabaseUrl = 'https://howpsxolbsreaaavducp.supabase.co'
const supabaseKey = process.env.SUPABASE_KEY
const supabase = createClient(supabaseUrl, supabaseKey)

// query table users
supabase.from('users').select('*').then(console.log).catch(console.error)
