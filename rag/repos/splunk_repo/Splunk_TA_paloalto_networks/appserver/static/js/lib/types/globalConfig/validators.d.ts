import { z } from 'zod';
export declare const NumberValidator: z.ZodObject<{
    errorMsg: z.ZodOptional<z.ZodString>;
    type: z.ZodLiteral<"number">;
    range: z.ZodArray<z.ZodNumber, "many">;
    isInteger: z.ZodOptional<z.ZodBoolean>;
}, "strip", z.ZodTypeAny, {
    type: "number";
    range: number[];
    errorMsg?: string | undefined;
    isInteger?: boolean | undefined;
}, {
    type: "number";
    range: number[];
    errorMsg?: string | undefined;
    isInteger?: boolean | undefined;
}>;
export declare const StringValidator: z.ZodObject<{
    errorMsg: z.ZodOptional<z.ZodString>;
    type: z.ZodLiteral<"string">;
    minLength: z.ZodNumber;
    maxLength: z.ZodNumber;
}, "strip", z.ZodTypeAny, {
    type: "string";
    minLength: number;
    maxLength: number;
    errorMsg?: string | undefined;
}, {
    type: "string";
    minLength: number;
    maxLength: number;
    errorMsg?: string | undefined;
}>;
export declare const RegexValidator: z.ZodObject<{
    errorMsg: z.ZodOptional<z.ZodString>;
    type: z.ZodLiteral<"regex">;
    pattern: z.ZodString;
}, "strip", z.ZodTypeAny, {
    type: "regex";
    pattern: string;
    errorMsg?: string | undefined;
}, {
    type: "regex";
    pattern: string;
    errorMsg?: string | undefined;
}>;
export declare const EmailValidator: z.ZodObject<{
    errorMsg: z.ZodOptional<z.ZodString>;
    type: z.ZodLiteral<"email">;
}, "strip", z.ZodTypeAny, {
    type: "email";
    errorMsg?: string | undefined;
}, {
    type: "email";
    errorMsg?: string | undefined;
}>;
export declare const Ipv4Validator: z.ZodObject<{
    errorMsg: z.ZodOptional<z.ZodString>;
    type: z.ZodLiteral<"ipv4">;
}, "strip", z.ZodTypeAny, {
    type: "ipv4";
    errorMsg?: string | undefined;
}, {
    type: "ipv4";
    errorMsg?: string | undefined;
}>;
export declare const UrlValidator: z.ZodObject<{
    errorMsg: z.ZodOptional<z.ZodString>;
    type: z.ZodLiteral<"url">;
}, "strip", z.ZodTypeAny, {
    type: "url";
    errorMsg?: string | undefined;
}, {
    type: "url";
    errorMsg?: string | undefined;
}>;
export declare const DateValidator: z.ZodObject<{
    errorMsg: z.ZodOptional<z.ZodString>;
    type: z.ZodLiteral<"date">;
}, "strip", z.ZodTypeAny, {
    type: "date";
    errorMsg?: string | undefined;
}, {
    type: "date";
    errorMsg?: string | undefined;
}>;
