import {
  ApiError,
  getApiErrorUserMessage,
  sanitizeRedirectPath,
} from "../../api/client";

export type AuthFieldName = "email" | "password" | "username";

export type AuthFieldErrors = Partial<Record<AuthFieldName, string>>;

export type RegistrationValidationState = {
  fieldErrors: AuthFieldErrors;
  formError: string | null;
};

const REGISTRATION_FIELD_MESSAGES: Record<AuthFieldName, string> = {
  email: "Informe um e-mail válido.",
  password: "Informe uma senha válida.",
  username: "Informe um nome de usuário válido.",
};

export const REGISTRATION_SUCCESS_PARAM = "cadastro";

export function getSafeRedirectFromSearch(search: string) {
  const redirect = new URLSearchParams(search).get("redirect");
  return redirect ? sanitizeRedirectPath(redirect) : "/";
}

export function buildRegisteredLoginUrl() {
  return `/login?${REGISTRATION_SUCCESS_PARAM}=ok`;
}

export function getLoginConfirmationMessage(search: string) {
  const params = new URLSearchParams(search);
  return params.get(REGISTRATION_SUCCESS_PARAM) === "ok"
    ? "Cadastro criado com sucesso. Entre para continuar."
    : null;
}

export function getLoginFormErrorMessage(error: unknown) {
  return getApiErrorUserMessage(error);
}

export function getRegistrationValidationState(
  error: unknown
): RegistrationValidationState {
  if (!(error instanceof ApiError) || error.code !== "VALIDATION_FAILED") {
    return {
      fieldErrors: {},
      formError: getApiErrorUserMessage(error),
    };
  }

  const fieldErrors = mapValidationFieldErrors(error.details);

  return {
    fieldErrors,
    formError:
      Object.keys(fieldErrors).length > 0
        ? null
        : "Confira os dados informados e tente novamente.",
  };
}

function mapValidationFieldErrors(details: unknown) {
  const fieldErrors: AuthFieldErrors = {};

  if (!isRecord(details)) {
    return fieldErrors;
  }

  for (const field of Object.keys(REGISTRATION_FIELD_MESSAGES) as AuthFieldName[]) {
    if (Object.hasOwn(details, field)) {
      fieldErrors[field] = REGISTRATION_FIELD_MESSAGES[field];
    }
  }

  return fieldErrors;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}
