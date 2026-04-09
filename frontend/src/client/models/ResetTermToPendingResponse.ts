/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export type ResetTermToPendingResponse = {
    message: string;
    batchId: string;
    termId: string;
    leadsRemoved: number;
    dispatched: boolean;
    dispatchBlockedReason?: (string | null);
};

