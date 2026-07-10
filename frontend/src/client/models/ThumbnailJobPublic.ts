/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export type ThumbnailJobPublic = {
    id: string;
    status: string;
    iteration: number;
    result_url: (string | null);
    error: (string | null);
    parent_job_id: (string | null);
    root_job_id: (string | null);
    created_by: string;
    created_by_email?: (string | null);
    created_at: string;
    updated_at: string;
    completed_at: (string | null);
    reference_image_url?: (string | null);
    base_image_urls?: (Array<string> | null);
    title?: (string | null);
    include_title?: (boolean | null);
    creative_comments?: (string | null);
    model?: (string | null);
    feedback?: (string | null);
    prompt_used?: (string | null);
};

