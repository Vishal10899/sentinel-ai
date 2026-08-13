use regex::Regex;


#[derive(Clone)]
pub struct DlpEngine {
    ssn_regex: Regex,
    credit_card_regex: Regex,
    api_key_regex: Regex,
    jwt_regex: Regex,
}

impl DlpEngine {
    pub fn new() -> Self {
        Self {
            ssn_regex: Regex::new(r"\b\d{3}-\d{2}-\d{4}\b").unwrap(),
            credit_card_regex: Regex::new(r"\b(?:\d[ -]*?){13,16}\b").unwrap(),
            api_key_regex: Regex::new(r"(?i)(sk-[a-zA-Z0-9]{20,}|sk-snt-[a-zA-Z0-9]{24,})").unwrap(),

            jwt_regex: Regex::new(r"eyJ[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}").unwrap(),
        }
    }

    pub fn inspect_and_redact(&self, text: &str) -> String {
        let mut redacted = text.to_string();
        redacted = self.ssn_regex.replace_all(&redacted, "[REDACTED_SSN]").to_string();
        redacted = self.credit_card_regex.replace_all(&redacted, "[REDACTED_CREDIT_CARD]").to_string();
        redacted = self.api_key_regex.replace_all(&redacted, "[REDACTED_API_KEY]").to_string();
        redacted = self.jwt_regex.replace_all(&redacted, "[REDACTED_JWT_TOKEN]").to_string();
        redacted
    }
}
