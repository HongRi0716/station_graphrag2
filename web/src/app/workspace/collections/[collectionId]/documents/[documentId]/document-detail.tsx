'use client';
import { Document, DocumentPreview } from '@/api';
import { getDocumentStatusColor } from '@/app/workspace/collections/tools';
import { FormatDate } from '@/components/format-date';
import { Markdown } from '@/components/markdown';
import { useCollectionContext } from '@/components/providers/collection-provider';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Separator } from '@/components/ui/separator';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { cn } from '@/lib/utils';
import _ from 'lodash';
import { ArrowLeft, LoaderCircle } from 'lucide-react';
import dynamic from 'next/dynamic';
import Link from 'next/link';
import { useEffect, useMemo, useState } from 'react';
import 'react-pdf/dist/Page/AnnotationLayer.css';
import 'react-pdf/dist/Page/TextLayer.css';

const PDFDocument = dynamic(() => import('react-pdf').then((r) => r.Document), {
  ssr: false,
});
const PDFPage = dynamic(() => import('react-pdf').then((r) => r.Page), {
  ssr: false,
});

export const DocumentDetail = ({
  document,
  documentPreview,
}: {
  document: Document;

  documentPreview: DocumentPreview;
}) => {
  const { collection } = useCollectionContext();
  const [numPages, setNumPages] = useState<number>(0);

  const isPdf = useMemo(() => {
    return Boolean(documentPreview.doc_filename?.match(/\.pdf/));
  }, [documentPreview.doc_filename]);

  useEffect(() => {
    const loadPDF = async () => {
      const { pdfjs } = await import('react-pdf');

      pdfjs.GlobalWorkerOptions.workerSrc = new URL(
        'pdfjs-dist/build/pdf.worker.min.mjs',
        import.meta.url,
      ).toString();
    };
    loadPDF();
  }, []);

  return (
    <>
      <Tabs defaultValue="markdown" className="gap-4">
        <div className="flex flex-row items-center justify-between gap-2">
          <div className="flex flex-row items-center gap-4">
            <Button asChild variant="ghost" size="icon">
              <Link href={`/workspace/collections/${collection.id}/documents`}>
                <ArrowLeft />
              </Link>
            </Button>
            <div className={cn('max-w-80 truncate')}>
              {documentPreview.doc_filename}
            </div>
          </div>

          <div className="flex flex-row gap-6">
            <div className="text-muted-foreground flex flex-row items-center gap-4 text-sm">
              <div>{(Number(document.size || 0) / 1000).toFixed(2)} KB</div>
              <Separator
                orientation="vertical"
                className="data-[orientation=vertical]:h-6"
              />
              {document.updated ? (
                <>
                  <div>
                    <FormatDate datetime={new Date(document.updated)} />
                  </div>
                  <Separator
                    orientation="vertical"
                    className="data-[orientation=vertical]:h-6"
                  />
                </>
              ) : null}
              <div className={getDocumentStatusColor(document.status)}>
                {_.capitalize(document.status)}
              </div>
            </div>
            <TabsList>
              <TabsTrigger value="markdown">Markdown</TabsTrigger>
              {isPdf && <TabsTrigger value="pdf">PDF</TabsTrigger>}
              {documentPreview.vision_chunks &&
                documentPreview.vision_chunks.length > 0 && (
                  <TabsTrigger value="vision">
                    Vision-to-Text ({documentPreview.vision_chunks.length})
                  </TabsTrigger>
                )}
            </TabsList>
          </div>
        </div>

        <TabsContent value="markdown">
          <Card>
            <CardContent>
              <Markdown>{documentPreview.markdown_content}</Markdown>
            </CardContent>
          </Card>
        </TabsContent>

        {isPdf && (
          <TabsContent value="pdf">
            <PDFDocument
              file={`${process.env.NEXT_PUBLIC_BASE_PATH || ''}/api/v1/collections/${collection.id}/documents/${document.id}/object?path=${documentPreview.converted_pdf_object_path}`}
              onLoadSuccess={({ numPages }: { numPages: number }) => {
                setNumPages(numPages);
              }}
              loading={
                <div className="flex flex-col py-8">
                  <LoaderCircle className="size-10 animate-spin self-center opacity-50" />
                </div>
              }
              className="flex flex-col justify-center gap-1"
            >
              {_.times(numPages).map((index) => {
                return (
                  <div key={index} className="text-center">
                    <Card className="inline-block overflow-hidden p-0">
                      <PDFPage pageNumber={index + 1} className="bg-accent" />
                    </Card>
                  </div>
                );
              })}
            </PDFDocument>
          </TabsContent>
        )}

        {documentPreview.vision_chunks &&
          documentPreview.vision_chunks.length > 0 && (
            <TabsContent value="vision">
              <div className="flex flex-col gap-4">
                {documentPreview.vision_chunks.map((chunk, index) => {
                  const metadata = chunk.metadata as
                    | { page_idx?: number }
                    | undefined;
                  const pageIdx = metadata?.page_idx;
                  const assetId = chunk.asset_id;
                  return (
                    <Card key={chunk.id || index}>
                      <CardContent className="pt-6">
                        <div className="mb-4 flex flex-row items-center justify-between">
                          <div className="text-muted-foreground text-sm font-medium">
                            {assetId ? (
                              <>
                                Asset: {assetId}
                                {pageIdx !== undefined && pageIdx !== null && (
                                  <span className="ml-2">
                                    (Page {Number(pageIdx) + 1})
                                  </span>
                                )}
                              </>
                            ) : (
                              <>
                                Vision Analysis {index + 1}
                                {pageIdx !== undefined && pageIdx !== null && (
                                  <span className="ml-2">
                                    (Page {Number(pageIdx) + 1})
                                  </span>
                                )}
                              </>
                            )}
                          </div>
                        </div>
                        <div className="prose prose-sm dark:prose-invert max-w-none">
                          <Markdown>{chunk.text || ''}</Markdown>
                        </div>
                      </CardContent>
                    </Card>
                  );
                })}
              </div>
            </TabsContent>
          )}
      </Tabs>
    </>
  );
};
