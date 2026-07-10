/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { Body_create_thumbnail_api_v1_thumbnails_thumbnail_post } from '../models/Body_create_thumbnail_api_v1_thumbnails_thumbnail_post';
import type { ThumbnailFeedbackRequest } from '../models/ThumbnailFeedbackRequest';
import type { ThumbnailHistoryResponse } from '../models/ThumbnailHistoryResponse';
import type { ThumbnailJobCreatedResponse } from '../models/ThumbnailJobCreatedResponse';
import type { ThumbnailJobPublic } from '../models/ThumbnailJobPublic';
import type { ThumbnailListResponse } from '../models/ThumbnailListResponse';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class ThumbnailCreatorService {
    /**
     * Create Thumbnail
     * Create a thumbnail job from multipart uploads; ``created_by`` comes from the JWT only.
     * @param formData
     * @returns ThumbnailJobCreatedResponse Successful Response
     * @throws ApiError
     */
    public static createThumbnailApiV1ThumbnailsThumbnailPost(
        formData: Body_create_thumbnail_api_v1_thumbnails_thumbnail_post,
    ): CancelablePromise<ThumbnailJobCreatedResponse> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/thumbnails/thumbnail',
            formData: formData,
            mediaType: 'multipart/form-data',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * List Thumbnails
     * ADMIN sees thumbnails from every member; MEMBER sees only their own.
     * @param cursor
     * @param limit
     * @returns ThumbnailListResponse Successful Response
     * @throws ApiError
     */
    public static listThumbnailsApiV1ThumbnailsThumbnailGet(
        cursor?: (string | null),
        limit: number = 20,
    ): CancelablePromise<ThumbnailListResponse> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/thumbnails/thumbnail',
            query: {
                'cursor': cursor,
                'limit': limit,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Feedback Thumbnail
     * @param jobId
     * @param requestBody
     * @returns ThumbnailJobCreatedResponse Successful Response
     * @throws ApiError
     */
    public static feedbackThumbnailApiV1ThumbnailsThumbnailJobIdFeedbackPost(
        jobId: string,
        requestBody: ThumbnailFeedbackRequest,
    ): CancelablePromise<ThumbnailJobCreatedResponse> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/thumbnails/thumbnail/{job_id}/feedback',
            path: {
                'job_id': jobId,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * History Thumbnail
     * @param jobId
     * @returns ThumbnailHistoryResponse Successful Response
     * @throws ApiError
     */
    public static historyThumbnailApiV1ThumbnailsThumbnailJobIdHistoryGet(
        jobId: string,
    ): CancelablePromise<ThumbnailHistoryResponse> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/thumbnails/thumbnail/{job_id}/history',
            path: {
                'job_id': jobId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Thumbnail
     * @param jobId
     * @returns ThumbnailJobPublic Successful Response
     * @throws ApiError
     */
    public static getThumbnailApiV1ThumbnailsThumbnailJobIdGet(
        jobId: string,
    ): CancelablePromise<ThumbnailJobPublic> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/thumbnails/thumbnail/{job_id}',
            path: {
                'job_id': jobId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
