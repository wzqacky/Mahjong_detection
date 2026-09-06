import Constants from 'expo-constants';

const extra = (Constants.expoConfig?.extra ?? {}) as Record<string, string | undefined>;

function required(key: string): string {
  const value = extra[key];
  if (!value) {
    throw new Error(
      `Missing config: ${key}. Set it in mobile/.env and restart Expo with 'npx expo start -c'.`,
    );
  }
  return value;
}

// Kept for FastAPI fallback / rollback path
export const BASE_URL: string = extra.baseUrl ?? 'http://10.0.2.2:8000';

export const RUNPOD_ENDPOINT_ID = required('runpodEndpointId');
export const RUNPOD_API_KEY = required('runpodApiKey');
export const RUNPOD_URL = `https://api.runpod.ai/v2/${RUNPOD_ENDPOINT_ID}/runsync`;
