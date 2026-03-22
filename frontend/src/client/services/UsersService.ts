/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { UserCreate } from '../models/UserCreate';
import type { UserResponse } from '../models/UserResponse';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class UsersService {
    /**
     * Bootstrap first ADMIN (only works when no users exist)
     * Create the very first ADMIN user when the users table is empty.
     * This endpoint is unauthenticated intentionally — use it once from the
     * FastAPI docs to bootstrap the system, then it will reject all subsequent calls.
     * @param requestBody
     * @returns UserResponse Successful Response
     * @throws ApiError
     */
    public static seedAdminApiV1UsersSeedPost(
        requestBody: UserCreate,
    ): CancelablePromise<UserResponse> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/users/seed',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Create a new user (ADMIN only)
     * Create a user with any role. Requires ADMIN JWT.
     * @param requestBody
     * @returns UserResponse Successful Response
     * @throws ApiError
     */
    public static createNewUserApiV1UsersPost(
        requestBody: UserCreate,
    ): CancelablePromise<UserResponse> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/users',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
