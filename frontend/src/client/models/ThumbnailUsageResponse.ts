/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { ModelUsage } from './ModelUsage';
/**
 * Shared org-wide monthly usage for capped models. Period is the current
 * calendar month (UTC); resets automatically at the month boundary.
 */
export type ThumbnailUsageResponse = {
    period_start: string;
    usage: Record<string, ModelUsage>;
};

