import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { ThemeProvider } from '@/hooks/useTheme';
import { 
  Home,
  Dashboard, 
  AlphaControlRoom, 
  ExperimentNotebook, 
  Benchmarks, 
  Pricing, 
  About, 
  Docs, 
  APIReference, 
  CCPA, 
  DPA, 
  CookiePolicy, 
  SignIn, 
  SignUp, 
  Terms, 
  Privacy, 
  Contact, 
  DemoAccess 
} from '@/pages';

import { CookieConsent } from '@/components/CookieConsent';
import { ProtectedRoute } from '@/components/ProtectedRoute';

console.log('SimHPC: App.tsx loaded.');

function App() {
  console.log('SimHPC: App component rendering...');
  const basename = window.location.pathname.startsWith('/lostbobo') ? '/lostbobo' : '';
  return (
    <ThemeProvider>
      <BrowserRouter basename={basename}>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/signup" element={<SignUp />} />
          <Route path="/signin" element={<SignIn />} />
          <Route path="/terms" element={<Terms />} />
          <Route path="/privacy" element={<Privacy />} />
          
          {/* Protected Routes */}
          <Route path="/dashboard" element={
            <ProtectedRoute>
              <Dashboard />
            </ProtectedRoute>
          } />
          <Route path="/dashboard/alpha" element={
            <ProtectedRoute>
              <AlphaControlRoom />
            </ProtectedRoute>
          } />
          <Route path="/dashboard/notebook" element={
            <ProtectedRoute>
              <ExperimentNotebook />
            </ProtectedRoute>
          } />

          <Route path="/benchmarks" element={<Benchmarks />} />
          <Route path="/pricing" element={<Pricing />} />
          <Route path="/about" element={<About />} />
          <Route path="/docs" element={<Docs />} />
          <Route path="/api-reference" element={<APIReference />} />
          <Route path="/ccpa" element={<CCPA />} />
          <Route path="/dpa" element={<DPA />} />
          <Route path="/cookies" element={<CookiePolicy />} />
          <Route path="/contact" element={<Contact />} />
          <Route path="/demo/:token" element={<DemoAccess />} />
        </Routes>
        <CookieConsent />
      </BrowserRouter>
    </ThemeProvider>
  );
}

export default App;
