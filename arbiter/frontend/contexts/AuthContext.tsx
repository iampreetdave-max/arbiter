'use client'

/**
 * Firebase Auth context.
 * Wraps the app with auth state and exposes signIn / signUp / signOut / Google OAuth.
 */
import {
  createContext,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from 'react'
import {
  type User,
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  signOut as firebaseSignOut,
  GoogleAuthProvider,
  signInWithPopup,
  onAuthStateChanged,
  sendPasswordResetEmail,
} from 'firebase/auth'
import { auth } from '@/lib/firebase'

// ── Context shape ──────────────────────────────────────────────────────────────────────
interface AuthContextValue {
  user: User | null
  /** True while the initial auth state is being resolved (shows skeleton/loader). */
  loading: boolean
  signIn: (email: string, password: string) => Promise<void>
  signUp: (email: string, password: string) => Promise<void>
  signInWithGoogle: () => Promise<void>
  signOut: () => Promise<void>
  resetPassword: (email: string) => Promise<void>
}

const AuthContext = createContext<AuthContextValue | null>(null)

// ── Provider ───────────────────────────────────────────────────────────────────────────
export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser]       = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const unsub = onAuthStateChanged(auth, (u) => {
      setUser(u)
      setLoading(false)
    })
    return unsub
  }, [])

  const signIn = async (email: string, password: string) => {
    await signInWithEmailAndPassword(auth, email, password)
  }

  const signUp = async (email: string, password: string) => {
    await createUserWithEmailAndPassword(auth, email, password)
  }

  const signInWithGoogle = async () => {
    const provider = new GoogleAuthProvider()
    await signInWithPopup(auth, provider)
  }

  const signOut = async () => {
    await firebaseSignOut(auth)
  }

  const resetPassword = async (email: string) => {
    await sendPasswordResetEmail(auth, email)
  }

  return (
    <AuthContext.Provider
      value={{ user, loading, signIn, signUp, signInWithGoogle, signOut, resetPassword }}
    >
      {children}
    </AuthContext.Provider>
  )
}

// ── Hook ────────────────────────────────────────────────────────────────────────────
export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used inside <AuthProvider>')
  return ctx
}
