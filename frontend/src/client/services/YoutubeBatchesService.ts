/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { BatchCreateRequest } from '../models/BatchCreateRequest';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class YoutubeBatchesService {
    /**
     * List Batches
     * List all batches with progress.
     * @returns any Successful Response
     * @throws ApiError
     */
    public static listBatchesApiV1YoutubeBatchesGet(): CancelablePromise<Array<Record<string, any>>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/youtube/batches',
        });
    }
    /**
     * Create Batch
     * Create a new batch in queued state.
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static createBatchApiV1YoutubeBatchesPost(
        requestBody: BatchCreateRequest,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/youtube/batches',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Batch
     * Batch detail including full term list.
     * @param batchId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static getBatchApiV1YoutubeBatchesBatchIdGet(
        batchId: string,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/youtube/batches/{batch_id}',
            path: {
                'batch_id': batchId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Delete Batch
     * Hard-delete a batch and all its associated terms and leads.
     * @param batchId
     * @returns void
     * @throws ApiError
     */
    public static deleteBatchApiV1YoutubeBatchesBatchIdDelete(
        batchId: string,
    ): CancelablePromise<void> {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/api/v1/youtube/batches/{batch_id}',
            path: {
                'batch_id': batchId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Trigger Batch
     * Start today's run for a batch.
     *
     * Returns 400 if another batch is already running today, or if the
     * batch is not in a triggerable state.
     * Returns 202 Accepted immediately; processing happens in Celery.
     * @param batchId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static triggerBatchApiV1YoutubeBatchesBatchIdTriggerPost(
        batchId: string,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/youtube/batches/{batch_id}/trigger',
            path: {
                'batch_id': batchId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
