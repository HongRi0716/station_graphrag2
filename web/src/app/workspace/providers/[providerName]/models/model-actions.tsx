'use client';

import {
  LlmProvider,
  LlmProviderModel,
  LlmProviderModelCreateApiEnum,
} from '@/api';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { apiClient } from '@/lib/api/client';
import { zodResolver } from '@hookform/resolvers/zod';
import { Slot } from '@radix-ui/react-slot';
import { ChevronDown, Eye } from 'lucide-react';
import { useTranslations } from 'next-intl';
import { useRouter } from 'next/navigation';
import { useCallback, useState } from 'react';
import { useForm } from 'react-hook-form';

import { toast } from 'sonner';
import * as z from 'zod';

const defaultValue = {
  model: '',
  api: LlmProviderModelCreateApiEnum.completion,
  apiTypeDisplay: 'completion',
  tags: [],
};

const providers = [
  {
    label: 'AlibabaCloud',
    value: 'alibabacloud',
  },
  {
    label: 'Anthropic',
    value: 'anthropic',
  },
  {
    label: 'DeepSeek',
    value: 'deepseek',
  },
  {
    label: 'Google Gemini',
    value: 'gemini',
  },
  {
    label: 'Jina AI',
    value: 'jina',
  },
  {
    label: 'OpenAI',
    value: 'openai',
  },
  {
    label: 'OpenRouter',
    value: 'openrouter',
  },
  {
    label: 'SiliconFlow',
    value: 'siliconflow',
  },
  {
    label: 'xAI',
    value: 'xai',
  },
];

const modelSchema = z.object({
  model: z.string().min(1),
  api: z.string().min(1),
  apiTypeDisplay: z.string().optional(), // For UI display: 'completion', 'vision', 'embedding', 'rerank'
  custom_llm_provider: z.string().min(1),
  context_window: z.coerce.number<number>().optional(),
  max_input_tokens: z.coerce.number<number>().optional(),
  max_output_tokens: z.coerce.number<number>().optional(),
  tags: z.array(z.string()).optional(),
});

export const ModelActions = ({
  model,
  provider,
  action,
  children,
}: {
  provider: LlmProvider;
  model?: LlmProviderModel;
  action: 'add' | 'edit' | 'delete';
  children?: React.ReactNode;
}) => {
  const page_models = useTranslations('page_models');
  const common_action = useTranslations('common.action');
  const common_tips = useTranslations('common.tips');

  const [createOrUpdateVisible, setCreateOrUpdateVisible] =
    useState<boolean>(false);
  const [deleteVisible, setDeleteVisible] = useState<boolean>(false);
  const router = useRouter();

  const form = useForm<z.infer<typeof modelSchema>>({
    resolver: zodResolver(modelSchema),
    defaultValues: {
      ...defaultValue,
      ...model,
      // Determine display type: if model has vision tag and is completion, show as vision
      apiTypeDisplay:
        model?.tags?.includes('vision') && model?.api === 'completion'
          ? 'vision'
          : model?.api || 'completion',
      // Preserve existing tags
      tags: model?.tags || [],
      // Ensure api field is set correctly
      api: model?.api || LlmProviderModelCreateApiEnum.completion,
    },
  });

  const handleDelete = useCallback(async () => {
    if (action === 'delete' && model?.model) {
      const res =
        await apiClient.defaultApi.llmProvidersProviderNameModelsApiModelDelete(
          {
            providerName: provider.name,
            api: model.api,
            model: model.model,
          },
        );
      if (res?.status === 200) {
        setDeleteVisible(false);
        setTimeout(router.refresh, 300);
      }
    }
  }, [action, model?.api, model?.model, provider.name, router]);

  const handleCreateOrUpdate = useCallback(
    async (values: z.infer<typeof modelSchema>) => {
      let res;
      // Determine actual API type and tags
      const apiTypeDisplay = values.apiTypeDisplay || values.api;
      const isVision = apiTypeDisplay === 'vision';
      // Use apiTypeDisplay directly, not values.api, to ensure correct API type
      const actualApi = isVision ? 'completion' : apiTypeDisplay || values.api;

      // Handle tags: add vision tag if vision selected, remove if not
      let tags = values.tags || [];
      if (isVision) {
        // Add vision tag if not present
        if (!tags.includes('vision')) {
          tags = [...tags, 'vision'];
        }
      } else {
        // Remove vision tag if present
        tags = tags.filter((tag) => tag !== 'vision');
      }

      if (action === 'edit' && model?.model) {
        res =
          await apiClient.defaultApi.llmProvidersProviderNameModelsApiModelPut({
            providerName: provider.name,
            api: model.api,
            model: model.model,
            llmProviderModelUpdate: {
              custom_llm_provider: values.custom_llm_provider,
              context_window: values.context_window,
              max_input_tokens: values.max_input_tokens,
              max_output_tokens: values.max_output_tokens,
              tags: tags,
            },
          });
      }
      if (action === 'add') {
        res = await apiClient.defaultApi.llmProvidersProviderNameModelsPost({
          providerName: provider.name,
          llmProviderModelCreate: {
            provider_name: provider.name,
            api: actualApi as LlmProviderModelCreateApiEnum,
            model: values.model,
            custom_llm_provider: values.custom_llm_provider,
            context_window: values.context_window,
            max_input_tokens: values.max_input_tokens,
            max_output_tokens: values.max_output_tokens,
            tags: tags,
          },
        });
      }
      if (res?.status === 200) {
        setCreateOrUpdateVisible(false);
        setTimeout(router.refresh, 300);
        toast.success(common_tips('save_success'));
      }
    },
    [
      action,
      common_tips,
      model?.api,
      model?.model,
      provider.name,
      router.refresh,
    ],
  );

  if (action === 'delete') {
    return (
      <Dialog open={deleteVisible} onOpenChange={() => setDeleteVisible(false)}>
        <DialogTrigger asChild>
          <Slot
            onClick={(e) => {
              setDeleteVisible(true);
              e.preventDefault();
            }}
          >
            {children}
          </Slot>
        </DialogTrigger>
        <DialogContent showCloseButton={false}>
          <DialogHeader>
            <DialogTitle>{common_tips('confirm')}</DialogTitle>
            <DialogDescription>
              {page_models('model.delete_confirm')}
            </DialogDescription>
          </DialogHeader>
          <DialogDescription></DialogDescription>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteVisible(false)}>
              {common_action('cancel')}
            </Button>
            <Button variant="destructive" onClick={() => handleDelete()}>
              {common_action('continue')}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    );
  } else {
    return (
      <Dialog
        open={createOrUpdateVisible}
        onOpenChange={() => setCreateOrUpdateVisible(false)}
      >
        <DialogTrigger asChild>
          <Slot
            onClick={(e) => {
              setCreateOrUpdateVisible(true);
              e.preventDefault();
            }}
          >
            {children}
          </Slot>
        </DialogTrigger>
        <DialogContent>
          <Form {...form}>
            <form
              onSubmit={form.handleSubmit(handleCreateOrUpdate)}
              className="space-y-8"
            >
              <DialogHeader>
                <DialogTitle>
                  {action === 'add' && page_models('model.add_model')}
                  {action === 'edit' && page_models('model.edit_model')}
                </DialogTitle>
                <DialogDescription></DialogDescription>
              </DialogHeader>
              <FormField
                control={form.control}
                name="model"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>{page_models('model.name')}</FormLabel>
                    <FormControl>
                      <Input
                        disabled={model !== undefined}
                        placeholder={page_models('model.name_placeholder')}
                        {...field}
                      />
                    </FormControl>
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="apiTypeDisplay"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>{page_models('model.api_type')}</FormLabel>
                    <FormControl>
                      <RadioGroup
                        className="grid grid-cols-4 gap-4"
                        onValueChange={field.onChange}
                        disabled={model !== undefined}
                        value={field.value || 'completion'}
                      >
                        <div className="bg-card flex h-9 items-center gap-3 rounded-md border px-3">
                          <RadioGroupItem value="completion" id="completion" />
                          <Label
                            htmlFor="completion"
                            className={
                              model == undefined ? '' : 'text-muted-foreground'
                            }
                          >
                            Completion
                          </Label>
                        </div>
                        <div className="bg-card flex h-9 items-center gap-3 rounded-md border px-3">
                          <RadioGroupItem value="vision" id="vision" />
                          <Label
                            htmlFor="vision"
                            className={
                              model == undefined ? '' : 'text-muted-foreground'
                            }
                          >
                            <Eye className="mr-1 inline size-4" />
                            Vision
                          </Label>
                        </div>
                        <div className="bg-card flex h-9 items-center gap-3 rounded-md border px-3">
                          <RadioGroupItem value="embedding" id="embedding" />
                          <Label
                            htmlFor="embedding"
                            className={
                              model == undefined ? '' : 'text-muted-foreground'
                            }
                          >
                            Embedding
                          </Label>
                        </div>
                        <div className="bg-card flex h-9 items-center gap-3 rounded-md border px-3">
                          <RadioGroupItem value="rerank" id="rerank" />
                          <Label
                            htmlFor="rerank"
                            className={
                              model == undefined ? '' : 'text-muted-foreground'
                            }
                          >
                            Rerank
                          </Label>
                        </div>
                      </RadioGroup>
                    </FormControl>
                  </FormItem>
                )}
              />
              {/* Hidden field to sync api with apiTypeDisplay */}
              <FormField
                control={form.control}
                name="api"
                render={({ field }) => {
                  const apiTypeDisplay =
                    form.watch('apiTypeDisplay') || 'completion';
                  const actualApi =
                    apiTypeDisplay === 'vision' ? 'completion' : apiTypeDisplay;
                  return <input type="hidden" {...field} value={actualApi} />;
                }}
              />
              <FormField
                control={form.control}
                name="custom_llm_provider"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>
                      {page_models('model.custom_llm_provider')}
                    </FormLabel>

                    <div className="relative flex flex-row">
                      <FormControl>
                        <Input
                          {...field}
                          placeholder={page_models(
                            'model.custom_llm_provider_placeholder',
                          )}
                        />
                      </FormControl>

                      <DropdownMenu>
                        <DropdownMenuTrigger className="absolute top-0.5 right-0.5">
                          <Button variant="ghost" className="size-8">
                            <ChevronDown />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end" className="w-115.5">
                          {providers.map((provider) => {
                            return (
                              <DropdownMenuItem
                                key={provider.value}
                                onClick={() =>
                                  form.setValue(
                                    'custom_llm_provider',
                                    provider.value,
                                  )
                                }
                              >
                                {provider.label}
                              </DropdownMenuItem>
                            );
                          })}
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </div>
                  </FormItem>
                )}
              />
              <div>
                <FormLabel className="text-muted-foreground mb-4">
                  {page_models('model.llm_params')}
                </FormLabel>
                <div className="grid grid-cols-3 gap-4">
                  <FormField
                    control={form.control}
                    name="context_window"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Context Window</FormLabel>
                        <FormControl>
                          <Input {...field} type="number" />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                  <FormField
                    control={form.control}
                    name="max_input_tokens"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Max Input Tokens</FormLabel>
                        <FormControl>
                          <Input {...field} type="number" />
                        </FormControl>
                      </FormItem>
                    )}
                  />
                  <FormField
                    control={form.control}
                    name="max_output_tokens"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Max Output Tokens</FormLabel>
                        <FormControl>
                          <Input {...field} type="number" />
                        </FormControl>
                      </FormItem>
                    )}
                  />
                </div>
              </div>

              <DialogFooter>
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setCreateOrUpdateVisible(false)}
                >
                  {common_action('cancel')}
                </Button>
                <Button type="submit">{common_action('save')}</Button>
              </DialogFooter>
            </form>
          </Form>
        </DialogContent>
      </Dialog>
    );
  }
};
