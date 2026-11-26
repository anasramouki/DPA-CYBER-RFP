import { NextRequest } from 'next/server';
import { GET as healthGet } from '../src/app/api/health/route';
import { POST as registerPost } from '../src/app/api/auth/register/route';
import { POST as loginPost } from '../src/app/api/auth/login/route';
import { POST as logoutPost } from '../src/app/api/auth/logout/route';
import { GET as profileGet, PATCH as profilePatch } from '../src/app/api/profile/route';

async function runLiveE2EVerification() {
  console.log('--- Starting CyberRFP Maroc Milestone 1 Live E2E Verification ---');
  const timestamp = Date.now();
  const testEmail = `analyst_${timestamp}@cyberrfp.ma`;
  const testPassword = 'Password123!Secure';

  // 1. Health Check
  console.log('\n[1/6] Testing GET /api/health against live Neon database...');
  const healthRes = await healthGet();
  console.log('Status:', healthRes.status);
  const healthData = await healthRes.json();
  console.log('Response:', healthData);
  if (healthRes.status !== 200 || healthData.database !== 'connected') {
    throw new Error('Health check failed!');
  }
  console.log('✓ GET /api/health passed.');

  // 2. User Registration
  console.log(`\n[2/6] Testing POST /api/auth/register with email: ${testEmail}...`);
  const registerReq = new NextRequest('http://localhost:3000/api/auth/register', {
    method: 'POST',
    body: JSON.stringify({
      email: testEmail,
      password: testPassword,
      fullName: 'Yassine El Amrani',
      jobTitle: 'Cyberspace Analyst',
      company: 'CyberRFP Maroc',
      whatsappPhone: '+212611223344',
      preferredLanguage: 'fr',
    }),
  });
  const registerRes = await registerPost(registerReq);
  console.log('Status:', registerRes.status);
  const registerData = await registerRes.json();
  console.log('User registered:', registerData.user?.fullName, 'Role:', registerData.user?.role);
  console.log('Bearer Token length:', registerData.token?.length);
  if (registerRes.status !== 201 || !registerData.token) {
    throw new Error(`Registration failed: ${JSON.stringify(registerData)}`);
  }
  const token = registerData.token;
  console.log('✓ POST /api/auth/register passed.');

  // 3. Authenticated Profile Fetch
  console.log('\n[3/6] Testing GET /api/profile using Bearer token...');
  const profileReq = new NextRequest('http://localhost:3000/api/profile', {
    method: 'GET',
    headers: {
      authorization: `Bearer ${token}`,
    },
  });
  const profileRes = await profileGet(profileReq);
  console.log('Status:', profileRes.status);
  const profileData = await profileRes.json();
  console.log('Profile retrieved:', profileData.user?.email, 'Company:', profileData.user?.company);
  if (profileRes.status !== 200 || profileData.user?.email !== testEmail) {
    throw new Error(`Profile fetch failed: ${JSON.stringify(profileData)}`);
  }
  console.log('✓ GET /api/profile passed.');

  // 4. Authenticated Profile Update (PATCH)
  console.log('\n[4/6] Testing PATCH /api/profile (updating WhatsApp alerts & title)...');
  const patchReq = new NextRequest('http://localhost:3000/api/profile', {
    method: 'PATCH',
    headers: {
      authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({
      jobTitle: 'Senior Threat Hunter',
      whatsappPhone: '+212655443322',
      whatsappAlertsEnabled: true,
      preferredLanguage: 'en',
    }),
  });
  const patchRes = await profilePatch(patchReq);
  console.log('Status:', patchRes.status);
  const patchData = await patchRes.json();
  console.log('Updated Profile:', {
    jobTitle: patchData.user?.jobTitle,
    whatsappPhone: patchData.user?.whatsappPhone,
    whatsappAlertsEnabled: patchData.user?.whatsappAlertsEnabled,
    preferredLanguage: patchData.user?.preferredLanguage,
  });
  if (
    patchRes.status !== 200 ||
    patchData.user?.jobTitle !== 'Senior Threat Hunter' ||
    patchData.user?.whatsappAlertsEnabled !== true
  ) {
    throw new Error(`Profile patch failed: ${JSON.stringify(patchData)}`);
  }
  console.log('✓ PATCH /api/profile passed.');

  // 5. Logout (Session Revocation)
  console.log('\n[5/6] Testing POST /api/auth/logout (revoking Bearer token)...');
  const logoutReq = new NextRequest('http://localhost:3000/api/auth/logout', {
    method: 'POST',
    headers: {
      authorization: `Bearer ${token}`,
    },
  });
  const logoutRes = await logoutPost(logoutReq);
  console.log('Status:', logoutRes.status);
  const logoutData = await logoutRes.json();
  console.log('Logout Response:', logoutData);
  if (logoutRes.status !== 200 || logoutData.status !== 'ok') {
    throw new Error('Logout failed!');
  }
  console.log('✓ POST /api/auth/logout passed.');

  // 6. Verification that Revoked Token is Rejected
  console.log('\n[6/6] Testing GET /api/profile with REVOKED token (must return 401 UNAUTHORIZED)...');
  const postLogoutReq = new NextRequest('http://localhost:3000/api/profile', {
    method: 'GET',
    headers: {
      authorization: `Bearer ${token}`,
    },
  });
  const postLogoutRes = await profileGet(postLogoutReq);
  console.log('Status:', postLogoutRes.status);
  const postLogoutData = await postLogoutRes.json();
  console.log('Response:', postLogoutData);
  if (postLogoutRes.status !== 401) {
    throw new Error(`Expected 401 for revoked token, got ${postLogoutRes.status}`);
  }
  console.log('✓ Revoked Bearer token successfully rejected with 401 UNAUTHORIZED.');

  console.log('\n======================================================');
  console.log('🎉 ALL MILESTONE 1 LIVE ENDPOINTS VERIFIED SUCCESSFULLY!');
  console.log('======================================================\n');
}

runLiveE2EVerification().catch((err) => {
  console.error('\n❌ E2E Verification Error:', err);
  process.exit(1);
});
