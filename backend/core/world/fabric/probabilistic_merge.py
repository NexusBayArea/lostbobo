from backend.core.world.fabric.uncertainty import UncertaintyEnvelope


class ProbabilisticMergeEngine:
    def merge(
        self,
        base: dict,
        incoming: dict,
        confidence: float,
        base_uncertainty: dict[str, UncertaintyEnvelope] = None,
        incoming_uncertainty: dict[str, UncertaintyEnvelope] = None,
    ) -> tuple[dict, dict[str, UncertaintyEnvelope]]:
        merged = dict(base)
        new_uncertainty = dict(base_uncertainty) if base_uncertainty else {}

        for key, value in incoming.items():
            base_unc = new_uncertainty.get(key)
            inc_unc = incoming_uncertainty.get(key) if incoming_uncertainty else None

            if key not in merged:
                merged[key] = value
                new_uncertainty[key] = inc_unc if inc_unc else UncertaintyEnvelope(confidence=confidence)
                continue

            existing = merged[key]
            if isinstance(existing, int | float) and isinstance(value, int | float):
                w = confidence
                blended = existing * (1 - w) + value * w
                old_conf = base_unc.confidence if base_unc else 1.0
                new_conf = old_conf * confidence
                new_var = ((existing - blended) ** 2 + value**2) * w
                new_uncertainty[key] = UncertaintyEnvelope(
                    confidence=new_conf,
                    variance=base_unc.variance + new_var if base_unc else new_var,
                    entropy=base_unc.entropy + (1 - confidence) if base_unc else 0.0,
                )
                merged[key] = blended
            elif isinstance(existing, dict) and isinstance(value, dict):
                sub_merged, sub_unc = self.merge(
                    existing,
                    value,
                    confidence,
                    base_unc.metadata if base_unc and hasattr(base_unc, "metadata") else {},
                    inc_unc.metadata if inc_unc and hasattr(inc_unc, "metadata") else {},
                )
                merged[key] = sub_merged
                new_uncertainty[key] = UncertaintyEnvelope(confidence=0.5, provenance_weight=1.0)
            else:
                merged[key] = value
                new_uncertainty[key] = inc_unc if inc_unc else UncertaintyEnvelope(confidence=confidence)

        return merged, new_uncertainty
