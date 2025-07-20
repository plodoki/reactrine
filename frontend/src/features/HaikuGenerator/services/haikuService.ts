import { HaikuRequest, HaikuResponse } from '@/types/api';

// Import the generated client
import { HaikuService as GeneratedHaikuService } from '@/lib/api-client';
import '@/lib/api-client-config'; // Ensure the client is configured

// All methods now use the generated client
export const generateHaiku = async (request: HaikuRequest): Promise<HaikuResponse> => {
  try {
    const response = await GeneratedHaikuService.generateHaikuEndpointApiV1HaikuPost({
      requestBody: request,
    });
    return response;
  } catch (error) {
    // Handle HTTP errors and parsing errors
    if (error instanceof Error) {
      throw new Error(`Failed to generate haiku: ${error.message}`);
    }
    throw new Error('Failed to generate haiku: Unknown error occurred');
  }
};
