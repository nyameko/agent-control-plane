# References

Primary project repositories:

- [infra-hpc-qc-k8s](https://github.com/nyameko/infra-hpc-qc-k8s)
- [quantum-platform](https://github.com/nyameko/quantum-platform)
- [quantum-workflows](https://github.com/nyameko/quantum-workflows)
- [uyuyu.africa](https://github.com/nyameko/uyuyu.africa)
- [CHPC Student Cluster Competition](https://github.com/chpc-tech-eval/scc)

Agent/client ecosystem considered by the architecture:

- [Hermes Agent](https://github.com/NousResearch/hermes-agent)
- [Hermes documentation](https://hermes-agent.nousresearch.com/)
- [LangGraph](https://docs.langchain.com/oss/python/langgraph/overview)
- [Letta](https://docs.letta.com/)
- [PydanticAI](https://ai.pydantic.dev/)
- [Microsoft Agent Framework](https://learn.microsoft.com/agent-framework/)
- [Hugging Face smolagents](https://huggingface.co/docs/smolagents/)
- [OpenHands](https://github.com/All-Hands-AI/OpenHands)
- [Goose](https://github.com/block/goose)
- [gptel](https://github.com/karthink/gptel)
- [Heretic](https://github.com/0xc1c4da/heretic)

Inference/model-serving references:

- [vLLM](https://docs.vllm.ai/)
- [Ollama](https://ollama.com/)
- [llama.cpp](https://github.com/ggml-org/llama.cpp)
- [LiteLLM](https://docs.litellm.ai/)

Security/risk references:

- [OWASP Top 10 for LLM Applications](https://owasp.org/www-project-top-10-for-large-language-model-applications/)
- [OWASP Agentic AI resources](https://genai.owasp.org/)
- [NIST AI Risk Management Framework](https://www.nist.gov/itl/ai-risk-management-framework)

Upstream interfaces are moving dependencies. Pin/review the actual implementation revision used in production and keep adapter conformance tests rather than treating a documentation URL as an immutable contract.
