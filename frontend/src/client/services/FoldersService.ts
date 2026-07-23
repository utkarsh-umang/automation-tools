/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { FolderCreate } from '../models/FolderCreate';
import type { FolderListResponse } from '../models/FolderListResponse';
import type { FolderPublic } from '../models/FolderPublic';
import type { FolderSummaryResponse } from '../models/FolderSummaryResponse';
import type { FolderUpdate } from '../models/FolderUpdate';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class FoldersService {
    /**
     * List Folders
     * @returns FolderListResponse Successful Response
     * @throws ApiError
     */
    public static listFoldersApiV1FoldersGet(): CancelablePromise<FolderListResponse> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/folders',
        });
    }
    /**
     * Folder Summaries
     * Per-folder thumbnail count + cover image for the album grid.
     * @returns FolderSummaryResponse Successful Response
     * @throws ApiError
     */
    public static folderSummariesApiV1FoldersSummaryGet(): CancelablePromise<FolderSummaryResponse> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/folders/summary',
        });
    }
    /**
     * Create Folder
     * @param requestBody
     * @returns FolderPublic Successful Response
     * @throws ApiError
     */
    public static createFolderApiV1FoldersPost(
        requestBody: FolderCreate,
    ): CancelablePromise<FolderPublic> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/folders',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Update Folder
     * @param folderId
     * @param requestBody
     * @returns FolderPublic Successful Response
     * @throws ApiError
     */
    public static updateFolderApiV1FoldersFolderIdPatch(
        folderId: string,
        requestBody: FolderUpdate,
    ): CancelablePromise<FolderPublic> {
        return __request(OpenAPI, {
            method: 'PATCH',
            url: '/api/v1/folders/{folder_id}',
            path: {
                'folder_id': folderId,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
