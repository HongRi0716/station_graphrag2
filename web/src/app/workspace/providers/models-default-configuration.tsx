import {
  DefaultModelConfig,
  DefaultModelConfigScenarioEnum,
  ModelSpec,
} from '@/api';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectLabel,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import { apiClient } from '@/lib/api/client';
import _ from 'lodash';
import { Eye, Settings, X } from 'lucide-react';
import { useTranslations } from 'next-intl';
import { useCallback, useEffect, useMemo, useState } from 'react';
import { toast } from 'sonner';

export const ModelsDefaultConfiguration = () => {
  const [defaultModels, setDefaultModels] = useState<DefaultModelConfig[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [visible, setVisible] = useState<boolean>(false);
  const common_action = useTranslations('common.action');
  const common_tips = useTranslations('common.tips');
  const page_models = useTranslations('page_models');
  const [scenarioModels, setScenarioModels] = useState<{
    [key in DefaultModelConfigScenarioEnum | 'default_for_vision']: {
      label?: string;
      name?: string;
      models?: ModelSpec[];
    }[];
  }>();

  const loadModels = useCallback(async () => {
    setLoading(true);
    try {
      const [
        defaultModelsRes,
        collectionModelsRes,
        agentModelsRes,
        visionModelsRes,
      ] = await Promise.all([
        apiClient.defaultApi.defaultModelsGet(),
        apiClient.defaultApi.availableModelsPost({
          tagFilterRequest: {
            tag_filters: [
              { operation: 'AND', tags: ['enable_for_collection'] },
            ],
          },
        }),
        apiClient.defaultApi.availableModelsPost({
          tagFilterRequest: {
            tag_filters: [{ operation: 'AND', tags: ['enable_for_agent'] }],
          },
        }),
        // Load vision models: completion API with vision tag
        // Purpose: Vision-to-Text (视觉转文本) - convert images to text descriptions
        // Note: API already filters by vision tag, so returned models are already filtered
        apiClient.defaultApi.availableModelsPost({
          tagFilterRequest: {
            tag_filters: [{ operation: 'AND', tags: ['vision'] }],
          },
        }),
      ]);

      const defaultModelsList = defaultModelsRes.data.items || [];

      // Ensure vision scenario exists in defaultModels
      // Purpose: Vision-to-Text (视觉转文本) - default model for converting images to text
      // Note: 'default_for_vision' is not yet in the backend enum, but we add it for frontend support
      const hasVisionScenario = defaultModelsList.some(
        (m) => (m.scenario as string) === 'default_for_vision',
      );
      if (!hasVisionScenario) {
        defaultModelsList.push({
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          scenario: 'default_for_vision' as any, // Type assertion for frontend-only scenario
          provider_name: undefined,
          model: undefined,
          custom_llm_provider: undefined,
        });
      }

      setDefaultModels(defaultModelsList);

      const agentModels = agentModelsRes.data.items || [];
      const collectionModels = collectionModelsRes.data.items || [];
      const visionModels = visionModelsRes.data.items || [];

      const default_for_agent_completion = agentModels.map((m) => ({
        label: m.label,
        name: m.name,
        models: m.completion,
      }));
      const default_for_collection_completion = collectionModels.map((m) => ({
        label: m.label,
        name: m.name,
        models: m.completion,
      }));
      const default_for_embedding = collectionModels.map((m) => ({
        label: m.label,
        name: m.name,
        models: m.embedding,
      }));
      const default_for_rerank = collectionModels.map((m) => ({
        label: m.label,
        name: m.name,
        models: m.rerank,
      }));
      const default_for_background_task = agentModels.map((m) => ({
        label: m.label,
        name: m.name,
        models: m.completion,
      }));
      // Vision models: for Vision-to-Text (视觉转文本) conversion
      // API already filters by vision tag, so completion models are already filtered
      // No need to filter again - just extract completion models from vision-filtered providers
      const default_for_vision = visionModels
        .map((m) => ({
          label: m.label,
          name: m.name,
          models: m.completion || [], // API already filtered, no need to filter again
        }))
        .filter((m) => m.models && m.models.length > 0);

      setScenarioModels({
        default_for_agent_completion,
        default_for_collection_completion,
        default_for_embedding,
        default_for_rerank,
        default_for_background_task,
        default_for_vision,
      });
    } catch (error) {
      console.error('Failed to load models:', error);
      toast.error('Failed to load models');
    } finally {
      setLoading(false);
    }
  }, []); // common_tips is not used in this callback

  const handleScenarioChange = useCallback(
    (
      scenario: DefaultModelConfigScenarioEnum | 'default_for_vision',
      model?: string,
    ) => {
      setDefaultModels((items) => {
        const item = items.find((m) => m.scenario === scenario);
        if (item) {
          item.model = model;
          const scenarioModelList =
            scenarioModels?.[scenario as keyof typeof scenarioModels];
          item.provider_name = scenarioModelList?.find((s) =>
            s.models?.some((m) => m.model === model),
          )?.name;
        }
        return [...items];
      });
    },
    [scenarioModels],
  );

  const handleSave = useCallback(async () => {
    // Check if vision scenario has configuration
    const visionConfig = defaultModels.find(
      (m) => (m.scenario as string) === 'default_for_vision' && m.model,
    );

    // Filter out vision scenario if backend doesn't support it yet
    // Only send scenarios that are in the DefaultModelConfigScenarioEnum
    const validScenarios = Object.values(DefaultModelConfigScenarioEnum);
    const modelsToSave = defaultModels.filter((m) =>
      validScenarios.includes(m.scenario as DefaultModelConfigScenarioEnum),
    );

    // Show info message if vision config exists but won't be saved
    // Vision model is used for Vision-to-Text (视觉转文本) conversion
    if (visionConfig) {
      toast.info(
        'Vision-to-Text model configuration is displayed but not yet saved (backend support pending)',
      );
    }

    try {
      const res = await apiClient.defaultApi.defaultModelsPut({
        defaultModelsUpdateRequest: { defaults: modelsToSave },
      });
      if (res?.status === 200) {
        setVisible(false);
        toast.success(common_tips('update_success'));
      }
    } catch (error) {
      console.error('Failed to save models:', error);
      toast.error('Failed to save models');
    }
  }, [common_tips, defaultModels]);

  const content = useMemo(() => {
    if (loading) {
      return (
        <>
          {_.times(5).map((index) => {
            return (
              <div key={index} className="flex w-full flex-col gap-2">
                <Skeleton className="h-[14px] w-1/2 rounded-md" />
                <Skeleton className="h-[36px] w-full rounded-md" />
              </div>
            );
          })}
          <Skeleton className="h-[40px] w-full rounded-md" />
        </>
      );
    } else {
      return (
        <>
          {defaultModels.map((modelConfig) => {
            const isVision =
              (modelConfig.scenario as string) === 'default_for_vision';
            return (
              <div
                key={modelConfig.scenario}
                className="flex w-full flex-col gap-2"
              >
                <Label className="flex items-center gap-2">
                  {isVision && <Eye className="size-4" />}
                  {_.startCase(modelConfig.scenario)}
                </Label>
                <div className="flex flex-row gap-1">
                  <Select
                    value={
                      defaultModels.find(
                        (m) => m.scenario === modelConfig.scenario,
                      )?.model || undefined
                    }
                    onValueChange={(v) => {
                      handleScenarioChange(modelConfig.scenario, v);
                    }}
                  >
                    <SelectTrigger className="w-full">
                      <SelectValue placeholder="Select a model" />
                    </SelectTrigger>
                    <SelectContent>
                      {scenarioModels?.[
                        modelConfig.scenario as keyof typeof scenarioModels
                      ]
                        ?.filter((item) => _.size(item.models))
                        .map((item) => {
                          return (
                            <SelectGroup key={item.name}>
                              <SelectLabel>{item.label}</SelectLabel>
                              {item.models?.map((model) => {
                                return (
                                  <SelectItem
                                    key={model.model}
                                    value={model.model || ''}
                                  >
                                    {model.model}
                                  </SelectItem>
                                );
                              })}
                            </SelectGroup>
                          );
                        })}
                    </SelectContent>
                  </Select>
                  <Button
                    size="icon"
                    variant="outline"
                    onClick={() => {
                      handleScenarioChange(modelConfig.scenario, undefined);
                    }}
                  >
                    <X />
                  </Button>
                </div>
              </div>
            );
          })}
          <div className="text-muted-foreground text-sm">
            {page_models('default_model.help')}
          </div>
        </>
      );
    }
  }, [
    defaultModels,
    handleScenarioChange,
    loading,
    page_models,
    scenarioModels,
  ]);

  useEffect(() => {
    if (visible) {
      loadModels();
    }
  }, [loadModels, visible]);

  return (
    <>
      <Tooltip>
        <TooltipTrigger asChild>
          <Button variant="outline" onClick={() => setVisible(true)}>
            <Settings />
          </Button>
        </TooltipTrigger>
        <TooltipContent>{page_models('default_model.config')}</TooltipContent>
      </Tooltip>
      <Dialog open={visible} onOpenChange={() => setVisible(false)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{page_models('default_model.config')}</DialogTitle>
          </DialogHeader>
          <div className="flex flex-col gap-6 py-8">{content}</div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setVisible(false)}>
              {common_action('cancel')}
            </Button>
            <Button onClick={handleSave}>{common_action('save')}</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
};
