/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class YoutubeLeadsService {
    /**
     * List Leads
     * Return paginated leads for a batch, sorted by score descending.
     * @param batchId
     * @param page
     * @param pageSize
     * @returns any Successful Response
     * @throws ApiError
     */
    public static listLeadsApiV1YoutubeBatchesBatchIdLeadsGet(
        batchId: string,
        page: number = 1,
        pageSize: number = 50,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/youtube/batches/{batch_id}/leads',
            path: {
                'batch_id': batchId,
            },
            query: {
                'page': page,
                'pageSize': pageSize,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Export Leads
     * Export all leads for a batch as a CSV file download.
     * @param batchId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static exportLeadsApiV1YoutubeBatchesBatchIdExportGet(
        batchId: string,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/youtube/batches/{batch_id}/export',
            path: {
                'batch_id': batchId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
