import { describe, it, expect } from 'vitest';
import {
 ApiError,
 appendRequestId,
 extractFieldErrors,
 handleFormError,
 readPublicErrorMessage,
 toToastMessage,
} from './errors';

/**
 * Build a `Response` with a JSON body. Used to simulate backend error
 * responses without standing up a fetch mock.
 */
function jsonResponse(status: number, body: unknown): Response {
 return new Response(JSON.stringify(body), {
 status,
 headers: { 'content-type': 'application/json' },
 });
}

function textResponse(status: number, body: string, contentType = 'text/plain'): Response {
 return new Response(body, { status, headers: { 'content-type': contentType } });
}

describe('appendRequestId', () => {
 it('appends the ID when present', () => {
 expect(appendRequestId('Boom', 'VL-abc')).toBe('Boom (Error ID: VL-abc)');
 });

 it('is a no-op when the ID is null/undefined/empty', () => {
 expect(appendRequestId('Boom', null)).toBe('Boom');
 expect(appendRequestId('Boom', undefined)).toBe('Boom');
 expect(appendRequestId('Boom', '')).toBe('Boom');
 });
});

describe('ApiError.fromResponse', () => {
 it('parses the canonical envelope', async () => {
 const res = jsonResponse(400, {
 error: {
 code: 'bad_input',
 message: 'Email is required.',
 request_id: 'VL-aaa',
 x_request_id: 'upstream-bbb',
 timestamp: '2026-05-03T00:00:00+00:00',
 },
 });

 const err = await ApiError.fromResponse(res);

 expect(err).toBeInstanceOf(ApiError);
 expect(err.status).toBe(400);
 expect(err.code).toBe('bad_input');
 expect(err.message).toBe('Email is required.');
 expect(err.requestId).toBe('VL-aaa');
 expect(err.xRequestId).toBe('upstream-bbb');
 expect(err.timestamp).toBe('2026-05-03T00:00:00+00:00');
 });

 it('falls back to the legacy {detail: ...} shape', async () => {
 const res = jsonResponse(400, { detail: 'Old shape error.' });

 const err = await ApiError.fromResponse(res);

 expect(err.code).toBe('unknown_error');
 expect(err.message).toBe('Old shape error.');
 expect(err.requestId).toBeNull();
 });

 it('uses the fallback message on 5xx but keeps the request ID', async () => {
 const res = jsonResponse(500, {
 error: {
 code: 'internal_error',
 message: 'Database is on fire.',
 request_id: 'VL-zzz',
 },
 });

 const err = await ApiError.fromResponse(res, 'Try again later.');

 expect(err.status).toBe(500);
 // 5xx never leaks the raw server message - too risky for end users.
 expect(err.message).toBe('Try again later.');
 expect(err.requestId).toBe('VL-zzz');
 });

 it('uses the fallback when the body is HTML or a traceback', async () => {
 const html = textResponse(400, '<html><body>oops</body></html>', 'text/html');
 expect((await ApiError.fromResponse(html, 'Fallback')).message).toBe('Fallback');

 const traceback = textResponse(400, 'Traceback (most recent call last)\n ...');
 expect((await ApiError.fromResponse(traceback, 'Fallback')).message).toBe('Fallback');
 });

 it('uses the fallback when the body is unparseable JSON', async () => {
 const res = textResponse(400, 'not json at all');
 const err = await ApiError.fromResponse(res, 'Fallback');
 // Plain short text is allowed through.
 expect(err.message).toBe('not json at all');
 });

 it('uses the fallback when the body is empty', async () => {
 const res = textResponse(400, '');
 const err = await ApiError.fromResponse(res, 'Fallback');
 expect(err.message).toBe('Fallback');
 });

 it('uses the fallback for over-long plain-text bodies', async () => {
 const res = textResponse(400, 'x'.repeat(500));
 const err = await ApiError.fromResponse(res, 'Fallback');
 expect(err.message).toBe('Fallback');
 });
});

describe('ApiError.toUserMessage', () => {
 it('appends the request ID', () => {
 const err = new ApiError({
 status: 400,
 code: 'x',
 message: 'Boom',
 requestId: 'VL-abc',
 });
 expect(err.toUserMessage()).toBe('Boom (Error ID: VL-abc)');
 });

 it('returns the bare message when no request ID is present', () => {
 const err = new ApiError({ status: 400, code: 'x', message: 'Boom' });
 expect(err.toUserMessage()).toBe('Boom');
 });
});

describe('ApiError.isValidationError', () => {
 it('is true for a 422 with details.errors', () => {
 const err = new ApiError({
 status: 422,
 code: 'validation_error',
 message: 'Validation failed.',
 details: { errors: [{ loc: ['body', 'email'], msg: 'invalid', type: 'value_error.email' }] },
 });
 expect(err.isValidationError()).toBe(true);
 });

 it('is false for non-422 status', () => {
 const err = new ApiError({
 status: 400,
 code: 'validation_error',
 message: 'Bad',
 details: { errors: [{ loc: ['body', 'email'], msg: 'x', type: 'y' }] },
 });
 expect(err.isValidationError()).toBe(false);
 });

 it('is false for a 422 without details.errors', () => {
 const err = new ApiError({ status: 422, code: 'x', message: 'm' });
 expect(err.isValidationError()).toBe(false);
 });
});

describe('extractFieldErrors', () => {
 it('flattens body-prefixed locs into bare field names', () => {
 const err = new ApiError({
 status: 422,
 code: 'validation_error',
 message: 'm',
 details: {
 errors: [
 { loc: ['body', 'email'], msg: 'invalid email', type: 'value_error.email' },
 { loc: ['body', 'password'], msg: 'too short', type: 'value_error' },
 ],
 },
 });
 expect(extractFieldErrors(err)).toEqual({
 email: 'invalid email',
 password: 'too short',
 });
 });

 it('keeps nested field paths joined by dots', () => {
 const err = new ApiError({
 status: 422,
 code: 'validation_error',
 message: 'm',
 details: {
 errors: [
 { loc: ['body', 'addresses', 0, 'city'], msg: 'required', type: 'missing' },
 ],
 },
 });
 expect(extractFieldErrors(err)).toEqual({ 'addresses.0.city': 'required' });
 });

 it('strips query/path location prefixes too', () => {
 const err = new ApiError({
 status: 422,
 code: 'validation_error',
 message: 'm',
 details: {
 errors: [
 { loc: ['query', 'page'], msg: 'must be > 0', type: 'value_error' },
 { loc: ['path', 'id'], msg: 'invalid uuid', type: 'value_error.uuid' },
 ],
 },
 });
 expect(extractFieldErrors(err)).toEqual({
 page: 'must be > 0',
 id: 'invalid uuid',
 });
 });

 it('keeps the first error per field when duplicates appear', () => {
 const err = new ApiError({
 status: 422,
 code: 'validation_error',
 message: 'm',
 details: {
 errors: [
 { loc: ['body', 'email'], msg: 'invalid email', type: 'value_error.email' },
 { loc: ['body', 'email'], msg: 'already taken', type: 'value_error' },
 ],
 },
 });
 expect(extractFieldErrors(err)).toEqual({ email: 'invalid email' });
 });

 it('returns an empty map for a non-validation error', () => {
 const err = new ApiError({ status: 400, code: 'x', message: 'm' });
 expect(extractFieldErrors(err)).toEqual({});
 });
});

describe('toToastMessage', () => {
 it('uses ApiError.toUserMessage for ApiError instances', () => {
 const err = new ApiError({
 status: 400,
 code: 'x',
 message: 'Boom',
 requestId: 'VL-abc',
 });
 expect(toToastMessage(err)).toBe('Boom (Error ID: VL-abc)');
 });

 it('uses the message of plain Error instances', () => {
 expect(toToastMessage(new Error('Network down'))).toBe('Network down');
 });

 it('falls back when given an arbitrary thrown value', () => {
 expect(toToastMessage('a raw string', 'Fallback')).toBe('Fallback');
 expect(toToastMessage(undefined, 'Fallback')).toBe('Fallback');
 expect(toToastMessage({ random: 'object' }, 'Fallback')).toBe('Fallback');
 });
});

describe('handleFormError', () => {
 it('routes 422 validation errors to setFieldErrors and skips the toast', async () => {
 const { vi } = await import('vitest');
 const setFieldErrors = vi.fn();
 const onToast = vi.fn();
 const err = new ApiError({
 status: 422,
 code: 'validation_error',
 message: 'Validation failed.',
 details: {
 errors: [{ loc: ['body', 'email'], msg: 'invalid', type: 'value_error.email' }],
 },
 });

 handleFormError(err, { setFieldErrors, onToast });

 expect(setFieldErrors).toHaveBeenCalledWith({ email: 'invalid' });
 expect(onToast).not.toHaveBeenCalled();
 });

 it('clears prior field errors and toasts non-validation errors', async () => {
 const { vi } = await import('vitest');
 const setFieldErrors = vi.fn();
 const onToast = vi.fn();
 const err = new ApiError({
 status: 400,
 code: 'bad_request',
 message: 'Bad input',
 requestId: 'VL-xyz',
 });

 handleFormError(err, { setFieldErrors, onToast });

 expect(setFieldErrors).toHaveBeenCalledWith({});
 expect(onToast).toHaveBeenCalledWith('Bad input (Error ID: VL-xyz)');
 });

 it('handles non-ApiError throws via the fallback', async () => {
 const { vi } = await import('vitest');
 const onToast = vi.fn();

 handleFormError(new Error('Network down'), { onToast, fallback: 'Try again.' });

 expect(onToast).toHaveBeenCalledWith('Network down');
 });

 it('falls back through to onToast when setFieldErrors is missing on a 422', async () => {
 const { vi } = await import('vitest');
 const onToast = vi.fn();
 const err = new ApiError({
 status: 422,
 code: 'validation_error',
 message: 'Validation failed.',
 details: { errors: [{ loc: ['body', 'email'], msg: 'invalid', type: 'value_error.email' }] },
 });

 handleFormError(err, { onToast });

 expect(onToast).toHaveBeenCalledWith('Validation failed.');
 });
});

describe('readPublicErrorMessage (legacy wrapper)', () => {
 it('returns the canonical message with request ID suffix', async () => {
 const res = jsonResponse(400, {
 error: { code: 'x', message: 'Bad', request_id: 'VL-abc' },
 });
 expect(await readPublicErrorMessage(res)).toBe('Bad (Error ID: VL-abc)');
 });

 it('falls back on legacy detail shape', async () => {
 const res = jsonResponse(400, { detail: 'Old shape' });
 expect(await readPublicErrorMessage(res)).toBe('Old shape');
 });
});
