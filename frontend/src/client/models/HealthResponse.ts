/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
/**
 * Health check response.
 */
export type HealthResponse = {
    status: string;
    environment: string;
    postgres: string;
    mongo: string;
    redis: string;
    celery: string;
    flower: string;
};

