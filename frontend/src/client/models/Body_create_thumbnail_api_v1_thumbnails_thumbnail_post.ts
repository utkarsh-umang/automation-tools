/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export type Body_create_thumbnail_api_v1_thumbnails_thumbnail_post = {
    reference_image: Blob;
    base_images?: Array<Blob>;
    title: string;
    include_title: boolean;
    creative_comments: string;
    model: string;
    folder_id?: (string | null);
    shorts_or_reels?: boolean;
};

