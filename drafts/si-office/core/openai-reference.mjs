// Public content checked on 2026-10-16. These checks do not approve CFP+ IDs,
// a legal HSTDN relationship, runtime access, competency or a partnership.
export const projectsDocumentationURL = 'https://help.openai.com/en/articles/10169521-projects-in-chatgpt';
const checkedAt = '2026-10-16';
export function openAIReferenceContent() {
  const about = 'https://openai.com/about/';
  const overview = 'https://chatgpt.com/overview/';
  const support = 'https://help.openai.com/en/articles/6614161-how-can-i-contact-support';
  return {
    dataStatus: 'PARTIAL REFERENCE; HSTDN IDENTITY AWAITS HUMAN GOVERNANCE',
    publicDescription: 'OpenAI giới thiệu hoạt động nghiên cứu và triển khai AI. ChatGPT hỗ trợ trao đổi, viết và lập trình; Dự án gom hội thoại, tệp và hướng dẫn cho công việc liên tục.',
    officialWebsite: {url: about, checkedAt, scope: 'PUBLIC DEVELOPER INFORMATION ONLY'},
    capabilities: [
      {name: 'Hỗ trợ viết và lập trình', scope: 'Soạn, sửa nội dung và hỗ trợ công việc mã nguồn theo mô tả sản phẩm', sourceURL: overview, competencyCertified: false},
      {name: 'Làm việc theo Dự án trong ChatGPT', scope: 'Tổ chức hội thoại, tệp và hướng dẫn theo Dự án', sourceURL: projectsDocumentationURL, competencyCertified: false}
    ],
    contacts: [{kind: 'PUBLIC SUPPORT GUIDANCE', url: 'https://help.openai.com/', guidanceURL: support,
      checkedAt, scope: 'OpenAI hướng dẫn dùng cửa sổ chat tại Help Center; không phải đầu mối CFP+ hoặc cam kết phản hồi'}],
    contactVerification: 'PUBLIC SUPPORT GUIDANCE CHECKED; CFP+ CONTACT / PARTNERSHIP NOT VERIFIED',
    sources: [
      {url: about, title: 'About OpenAI', checkedAt, scope: 'Public developer description; no CFP+ identity authority'},
      {url: overview, requestedURL: 'https://openai.com/chatgpt/overview/', title: 'ChatGPT overview', checkedAt, scope: 'Public product description; no competency or runtime certification'},
      {url: support, title: 'How can I contact support?', checkedAt, scope: 'Public support guidance; no named contact or partnership'},
      {url: projectsDocumentationURL, title: 'Projects in ChatGPT', checkedAt, scope: 'Project organization guidance; no CFP+ identity authority'}
    ]
  };
}
