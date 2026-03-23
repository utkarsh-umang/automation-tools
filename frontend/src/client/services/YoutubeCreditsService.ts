/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class YoutubeCreditsService {
    /**
     * Get Credits Today
     * Return today's YouTube API credit usage.
     *
     * Returns a zeroed response (not 404) if no usage has been recorded yet.
     * resetAt is midnight UTC of the following day.
     * @returns any Successful Response
     * @throws ApiError
     */
    public static getCreditsTodayApiV1YoutubeCreditsTodayGet(): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/youtube/credits/today',
        });
    }
}
